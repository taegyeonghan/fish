"""
API
，
"""

import os
import traceback
import threading
from flask import request, jsonify

from . import graph_bp
from ..config import Config
from ..services.ontology_generator import OntologyGenerator
from ..services.graph_builder import GraphBuilderService
from ..services.text_processor import TextProcessor
from ..services.document_collector import collect_related_documents, format_collected_documents
from ..utils.file_parser import FileParser
from ..utils.logger import get_logger
from ..utils.locale import t, get_locale, set_locale
from ..models.task import TaskManager, TaskStatus
from ..models.project import ProjectManager, ProjectStatus

logger = get_logger('ungdroofish.api')


def _ok(data=None, **extra):
    payload = {"success": True, "data": data}
    payload.update(extra)
    return jsonify(payload)


def _err(message: str, code: str, status_code: int = 400, **extra):
    payload = {"success": False, "error": message, "error_code": code}
    payload.update(extra)
    return jsonify(payload), status_code


def allowed_file(filename: str) -> bool:
    """"""
    if not filename or '.' not in filename:
        return False
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    return ext in Config.ALLOWED_EXTENSIONS


# ==============  ==============

@graph_bp.route('/project/<project_id>', methods=['GET'])
def get_project(project_id: str):
    """
    
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return _err(t('api.projectNotFound', id=project_id), "project_not_found", 404)

    return jsonify({
        "success": True,
        "data": project.to_dict()
    })


@graph_bp.route('/project/list', methods=['GET'])
def list_projects():
    """
    
    """
    limit = request.args.get('limit', 50, type=int)
    projects = ProjectManager.list_projects(limit=limit)
    
    return jsonify({
        "success": True,
        "data": [p.to_dict() for p in projects],
        "count": len(projects),
        "meta": {
            "count": len(projects)
        }
    })


@graph_bp.route('/project/<project_id>', methods=['DELETE'])
def delete_project(project_id: str):
    """
    
    """
    success = ProjectManager.delete_project(project_id)
    
    if not success:
        return _err(t('api.projectDeleteFailed', id=project_id), "project_delete_failed", 404)

    return jsonify({
        "success": True,
        "message": t('api.projectDeleted', id=project_id)
    })


@graph_bp.route('/project/<project_id>/reset', methods=['POST'])
def reset_project(project_id: str):
    """
    (설명 생략)
    """
    project = ProjectManager.get_project(project_id)
    
    if not project:
        return _err(t('api.projectNotFound', id=project_id), "project_not_found", 404)

    if project.ontology:
        project.status = ProjectStatus.ONTOLOGY_GENERATED
    else:
        project.status = ProjectStatus.CREATED
    
    project.graph_id = None
    project.graph_build_task_id = None
    project.error = None
    ProjectManager.save_project(project)
    
    return jsonify({
        "success": True,
        "message": t('api.projectReset', id=project_id),
        "data": project.to_dict()
    })


# ============== 1： ==============

@graph_bp.route('/ontology/generate', methods=['POST'])
def generate_ontology():
    """
    1：，
    
    ：multipart/form-data
    
    ：
        files: （PDF/MD/TXT），
        simulation_requirement: (설명 생략)
        project_name: (설명 생략)
        additional_context: (설명 생략)
        
    ：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "ontology": {
                    "entity_types": [...],
                    "edge_types": [...],
                    "analysis_summary": "..."
                },
                "files": [...],
                "total_text_length": 12345
            }
        }
    """
    try:
        logger.info("===  ===")
        
        simulation_requirement = request.form.get('simulation_requirement', '')
        project_name = request.form.get('project_name', 'Unnamed Project')
        additional_context = request.form.get('additional_context', '')
        
        logger.debug(f": {project_name}")
        logger.debug(f": {simulation_requirement[:100]}...")
        
        if not simulation_requirement:
            return _err(t('api.requireSimulationRequirement'), "missing_simulation_requirement", 400)
        
        uploaded_files = request.files.getlist('files')
        uploaded_files = request.files.getlist('files')
        has_uploaded_files = any(f and f.filename for f in uploaded_files)
        
        project = ProjectManager.create_project(name=project_name)
        project.simulation_requirement = simulation_requirement
        logger.info(f": {project.project_id}")
        
        document_texts = []
        document_texts = []
        all_text = ""
        
        for file in uploaded_files:
            if file and file.filename and allowed_file(file.filename):
                file_info = ProjectManager.save_file_to_project(
                    project.project_id, 
                    file, 
                    file.filename
                )
                project.files.append({
                    "filename": file_info["original_filename"],
                    "size": file_info["size"]
                })
                
                text = FileParser.extract_text(file_info["path"])
                text = TextProcessor.preprocess_text(text)
                document_texts.append(text)
                all_text += f"\n\n=== {file_info['original_filename']} ===\n{text}"

        if not document_texts:
            logger.info("No uploaded seed files found; collecting local documents from the question.")
            collected_docs = collect_related_documents(simulation_requirement)
            for doc in collected_docs:
                project.files.append(doc.to_project_file())
                document_texts.append(doc.to_seed_text())

            if collected_docs:
                all_text = format_collected_documents(simulation_requirement, collected_docs)
                logger.info(
                    "Auto-collected %s local documents for project %s",
                    len(collected_docs),
                    project.project_id,
                )
            elif has_uploaded_files:
                logger.warning("Uploaded files were present but none could be processed.")
        
        if not document_texts:
            ProjectManager.delete_project(project.project_id)
            return _err(t('api.noDocProcessed'), "no_document_processed", 400)
        
        project.total_text_length = len(all_text)
        ProjectManager.save_extracted_text(project.project_id, all_text)
        logger.info(f"， {len(all_text)} ")
        
        logger.info(" LLM ...")
        generator = OntologyGenerator()
        ontology = generator.generate(
            document_texts=document_texts,
            simulation_requirement=simulation_requirement,
            additional_context=additional_context if additional_context else None
        )
        
        entity_count = len(ontology.get("entity_types", []))
        edge_count = len(ontology.get("edge_types", []))
        logger.info(f": {entity_count} , {edge_count} ")
        
        project.ontology = {
            "entity_types": ontology.get("entity_types", []),
            "edge_types": ontology.get("edge_types", [])
        }
        project.analysis_summary = ontology.get("analysis_summary", "")
        project.status = ProjectStatus.ONTOLOGY_GENERATED
        ProjectManager.save_project(project)
        logger.info(f"===  === ID: {project.project_id}")
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project.project_id,
                "project_name": project.name,
                "ontology": project.ontology,
                "analysis_summary": project.analysis_summary,
                "files": project.files,
                "total_text_length": project.total_text_length
            }
        })
        
    except Exception as e:
        return _err(str(e), "internal_error", 500, traceback=traceback.format_exc())


# ============== 2： ==============

@graph_bp.route('/build', methods=['POST'])
def build_graph():
    """
    2：project_id
    
    （JSON）：
        {
            "project_id": "proj_xxxx",  // ，1
            "graph_name": "",    // 
            "chunk_size": 500,          // ，500
            "chunk_overlap": 50         // ，50
        }
        
    ：
        {
            "success": true,
            "data": {
                "project_id": "proj_xxxx",
                "task_id": "task_xxxx",
                "message": ""
            }
        }
    """
    try:
        logger.info("===  ===")
        
        data = request.get_json() or {}
        project_id = data.get('project_id')
        logger.debug(f": project_id={project_id}")
        
        if not project_id:
            return _err(t('api.requireProjectId'), "missing_project_id", 400)
        
        project = ProjectManager.get_project(project_id)
        if not project:
            return _err(t('api.projectNotFound', id=project_id), "project_not_found", 404)

        force = data.get('force', False)  # 
        
        if project.status == ProjectStatus.CREATED:
            return _err(t('api.ontologyNotGenerated'), "ontology_not_generated", 400)
        
        if project.status == ProjectStatus.GRAPH_BUILDING and not force:
            return _err(
                t('api.graphBuilding'),
                "graph_building",
                400,
                task_id=project.graph_build_task_id
            )
        
        # ，
        if force and project.status in [ProjectStatus.GRAPH_BUILDING, ProjectStatus.FAILED, ProjectStatus.GRAPH_COMPLETED]:
            project.status = ProjectStatus.ONTOLOGY_GENERATED
            project.graph_id = None
            project.graph_build_task_id = None
            project.error = None
        
        graph_name = data.get('graph_name', project.name or 'UngdrooFish Graph')
        chunk_size = data.get('chunk_size', project.chunk_size or Config.DEFAULT_CHUNK_SIZE)
        chunk_overlap = data.get('chunk_overlap', project.chunk_overlap or Config.DEFAULT_CHUNK_OVERLAP)
        
        project.chunk_size = chunk_size
        project.chunk_overlap = chunk_overlap
        
        text = ProjectManager.get_extracted_text(project_id)
        if not text:
            return _err(t('api.textNotFound'), "text_not_found", 400)
        
        ontology = project.ontology
        if not ontology:
            return _err(t('api.ontologyNotFound'), "ontology_not_found", 400)
        
        task_manager = TaskManager()
        task_id = task_manager.create_task(f": {graph_name}")
        logger.info(f": task_id={task_id}, project_id={project_id}")
        
        project.status = ProjectStatus.GRAPH_BUILDING
        project.graph_build_task_id = task_id
        ProjectManager.save_project(project)
        
        # Capture locale before spawning background thread
        current_locale = get_locale()

        def build_task():
            set_locale(current_locale)
            build_logger = get_logger('ungdroofish.build')
            try:
                build_logger.info(f"[{task_id}] ...")
                task_manager.update_task(
                    task_id, 
                    status=TaskStatus.PROCESSING,
                    message=t('progress.initGraphService')
                )
                
                builder = GraphBuilderService()
                
                task_manager.update_task(
                    task_id,
                    message=t('progress.textChunking'),
                    progress=5
                )
                chunks = TextProcessor.split_text(
                    text, 
                    chunk_size=chunk_size, 
                    overlap=chunk_overlap
                )
                total_chunks = len(chunks)
                
                task_manager.update_task(
                    task_id,
                    message=t('progress.creatingZepGraph'),
                    progress=10
                )
                graph_id = builder.create_graph(name=graph_name)
                
                # graph_id
                project.graph_id = graph_id
                ProjectManager.save_project(project)
                
                task_manager.update_task(
                    task_id,
                    message=t('progress.settingOntology'),
                    progress=15
                )
                builder.set_ontology(graph_id, ontology)
                
                # LLM-based entity/relation extraction from chunks
                def extract_progress_callback(msg, progress_ratio):
                    progress = 15 + int(progress_ratio * 75)  # 15% - 90%
                    task_manager.update_task(
                        task_id,
                        message=msg,
                        progress=progress
                    )

                task_manager.update_task(
                    task_id,
                    message=t('progress.addingChunks', count=total_chunks),
                    progress=15
                )

                builder._extract_and_add_entities(
                    graph_id,
                    chunks,
                    ontology,
                    batch_size=3,
                    progress_callback=extract_progress_callback
                )
                
                task_manager.update_task(
                    task_id,
                    message=t('progress.fetchingGraphData'),
                    progress=95
                )
                graph_data = builder.get_graph_data(graph_id)
                
                project.status = ProjectStatus.GRAPH_COMPLETED
                ProjectManager.save_project(project)
                
                node_count = graph_data.get("node_count", 0)
                edge_count = graph_data.get("edge_count", 0)
                build_logger.info(f"[{task_id}] : graph_id={graph_id}, ={node_count}, ={edge_count}")
                
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.COMPLETED,
                    message=t('progress.graphBuildComplete'),
                    progress=100,
                    result={
                        "project_id": project_id,
                        "graph_id": graph_id,
                        "node_count": node_count,
                        "edge_count": edge_count,
                        "chunk_count": total_chunks
                    }
                )
                
            except Exception as e:
                build_logger.error(f"[{task_id}] : {str(e)}")
                build_logger.debug(traceback.format_exc())
                
                project.status = ProjectStatus.FAILED
                project.error = str(e)
                ProjectManager.save_project(project)
                
                task_manager.update_task(
                    task_id,
                    status=TaskStatus.FAILED,
                    message=t('progress.buildFailed', error=str(e)),
                    error=traceback.format_exc()
                )
        
        thread = threading.Thread(target=build_task, daemon=True)
        thread.start()
        
        return jsonify({
            "success": True,
            "data": {
                "project_id": project_id,
                "task_id": task_id,
                "message": t('api.graphBuildStarted', taskId=task_id)
            }
        })
        
    except Exception as e:
        return _err(str(e), "internal_error", 500, traceback=traceback.format_exc())


# ==============  ==============

@graph_bp.route('/task/<task_id>', methods=['GET'])
def get_task(task_id: str):
    """
    
    """
    task = TaskManager().get_task(task_id)
    
    if not task:
        return _err(t('api.taskNotFound', id=task_id), "task_not_found", 404)
    
    return jsonify({
        "success": True,
        "data": task.to_dict()
    })


@graph_bp.route('/tasks', methods=['GET'])
def list_tasks():
    """
    
    """
    tasks = TaskManager().list_tasks()
    
    return jsonify({
        "success": True,
        "data": [t.to_dict() for t in tasks],
        "count": len(tasks),
        "meta": {
            "count": len(tasks)
        }
    })


# ==============  ==============

@graph_bp.route('/data/<graph_id>', methods=['GET'])
def get_graph_data(graph_id: str):
    """
    (설명 생략)
    """
    try:
        builder = GraphBuilderService()
        graph_data = builder.get_graph_data(graph_id)
        
        return jsonify({
            "success": True,
            "data": graph_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500


@graph_bp.route('/delete/<graph_id>', methods=['DELETE'])
def delete_graph(graph_id: str):
    """
    Zep
    """
    try:
        builder = GraphBuilderService()
        builder.delete_graph(graph_id)
        
        return jsonify({
            "success": True,
            "message": t('api.graphDeleted', id=graph_id)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }), 500