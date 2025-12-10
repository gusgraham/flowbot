import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAnalysisProjects, useDeleteAnalysisProject } from '../../api/hooks';
import { Activity, ArrowRight, Loader2, Plus, Trash2 } from 'lucide-react';
import CreateAnalysisProjectModal from './CreateAnalysisProjectModal';

const AnalysisProjectList: React.FC = () => {
    const { data: projects, isLoading, error } = useAnalysisProjects();
    const deleteProject = useDeleteAnalysisProject();
    const [isModalOpen, setIsModalOpen] = useState(false);

    const handleDelete = (e: React.MouseEvent, projectId: number, projectName: string) => {
        e.preventDefault();
        e.stopPropagation();
        if (confirm(`Delete project "${projectName}"? This will permanently delete all datasets, events, and associated files.`)) {
            deleteProject.mutate(projectId);
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-purple-500" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg">
                Error loading projects. Please try again.
            </div>
        );
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Analysis Projects</h1>
                    <p className="text-gray-500 mt-1">Select a project to perform hydraulic analysis.</p>
                </div>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center"
                >
                    <Plus size={20} className="mr-2" />
                    New Project
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects?.map((project) => (
                    <Link
                        key={project.id}
                        to={`/analysis/${project.id}`}
                        className="block bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow group"
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-purple-50 text-purple-600 rounded-lg">
                                <Activity size={24} />
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                    {project.job_number}
                                </span>
                                <button
                                    onClick={(e) => handleDelete(e, project.id, project.name)}
                                    disabled={deleteProject.isPending}
                                    className="p-1 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition"
                                    title="Delete project"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        <h3 className="text-lg font-bold text-gray-900 mb-1">{project.name}</h3>
                        <p className="text-sm text-gray-500 mb-4">{project.client}</p>

                        <div className="flex items-center text-purple-600 text-sm font-medium">
                            Open Workbench
                            <ArrowRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </Link>
                ))}

                {projects?.length === 0 && (
                    <div className="col-span-full text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <p className="text-gray-500 mb-4">No analysis projects found.</p>
                        <button
                            onClick={() => setIsModalOpen(true)}
                            className="text-purple-600 font-medium hover:text-purple-700"
                        >
                            Create your first project
                        </button>
                    </div>
                )}
            </div>

            <CreateAnalysisProjectModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
            />
        </div>
    );
};

export default AnalysisProjectList;
