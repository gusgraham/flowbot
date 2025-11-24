import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useWQProjects } from '../../api/hooks';
import { Droplets, ArrowRight, Loader2, Plus } from 'lucide-react';
import CreateWQProjectModal from './CreateWQProjectModal';

const WQProjectList: React.FC = () => {
    const { data: projects, isLoading, error } = useWQProjects();
    const [isModalOpen, setIsModalOpen] = useState(false);

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-cyan-500" size={32} />
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
                    <h1 className="text-2xl font-bold text-gray-900">Water Quality Projects</h1>
                    <p className="text-gray-500 mt-1">Manage water quality monitoring campaigns and data.</p>
                </div>
                <button 
                    onClick={() => setIsModalOpen(true)}
                    className="bg-cyan-600 text-white px-4 py-2 rounded-lg hover:bg-cyan-700 transition-colors flex items-center"
                >
                    <Plus size={20} className="mr-2" />
                    New Project
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects?.map((project) => (
                    <Link
                        key={project.id}
                        to={`/wq/${project.id}`}
                        className="block bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow group"
                    >
                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-cyan-50 text-cyan-600 rounded-lg">
                                <Droplets size={24} />
                            </div>
                            <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                {project.job_number}
                            </span>
                        </div>

                        <h3 className="text-lg font-bold text-gray-900 mb-1">{project.name}</h3>
                        <p className="text-sm text-gray-500 mb-4">{project.client}</p>

                        <div className="flex items-center text-cyan-600 text-sm font-medium">
                            Open Dashboard
                            <ArrowRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </Link>
                ))}

                {projects?.length === 0 && (
                    <div className="col-span-full text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <p className="text-gray-500 mb-4">No water quality projects found.</p>
                        <button 
                            onClick={() => setIsModalOpen(true)}
                            className="text-cyan-600 font-medium hover:text-cyan-700"
                        >
                            Create your first project
                        </button>
                    </div>
                )}
            </div>

            <CreateWQProjectModal 
                isOpen={isModalOpen} 
                onClose={() => setIsModalOpen(false)} 
            />
        </div>
    );
};

export default WQProjectList;
