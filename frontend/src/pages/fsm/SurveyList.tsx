import React, { useState, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useProjects, useImportProjectCsv, useDeleteProject } from '../../api/hooks';
import { Folder, ArrowRight, Loader2, Upload, Trash2, Info, AlertTriangle } from 'lucide-react';
import CreateSurveyModal from './CreateSurveyModal';

const SurveyList: React.FC = () => {
    const { data: projects, isLoading, error } = useProjects();
    const { mutate: importCsv, isPending: isImporting } = useImportProjectCsv();
    const { mutate: deleteProject, isPending: isDeleting } = useDeleteProject();
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            importCsv(e.target.files[0]);
            // Reset input
            e.target.value = '';
        }
    };

    const handleDelete = (id: number, e: React.MouseEvent) => {
        e.preventDefault(); // Prevent navigation
        setDeleteConfirmId(id);
    };

    const confirmDelete = (e: React.MouseEvent) => {
        e.preventDefault();
        if (deleteConfirmId) {
            deleteProject(deleteConfirmId);
            setDeleteConfirmId(null);
        }
    };

    const cancelDelete = (e: React.MouseEvent) => {
        e.preventDefault();
        setDeleteConfirmId(null);
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg">
                Error loading surveys. Please try again.
            </div>
        );
    }

    return (
        <div>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-gray-900">Field Surveys</h1>
                    <p className="text-gray-500 mt-1">Manage your ongoing and past flow surveys.</p>
                </div>
                <div className="flex gap-3 items-center">
                    <div className="group relative flex items-center">
                        <Info size={18} className="text-gray-400 hover:text-gray-600 cursor-help" />
                        <div className="absolute right-0 top-8 w-64 p-3 bg-gray-800 text-white text-xs rounded shadow-lg opacity-0 group-hover:opacity-100 transition-opacity z-10 pointer-events-none">
                            <p className="font-bold mb-1">CSV Format Required:</p>
                            <p>Columns: ProjectName, SiteID, MonitorID, MonitorType, InstallDate, PipeShape, PipeWidth, PipeHeight</p>
                        </div>
                    </div>

                    <input
                        type="file"
                        ref={fileInputRef}
                        className="hidden"
                        accept=".csv"
                        onChange={handleFileChange}
                    />
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isImporting}
                        className="flex items-center gap-2 bg-white border border-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                        {isImporting ? <Loader2 size={16} className="animate-spin" /> : <Upload size={16} />}
                        {isImporting ? 'Importing...' : 'Import CSV'}
                    </button>
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                    >
                        New Survey
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {projects?.map((project) => (
                    <Link
                        key={project.id}
                        to={`/fsm/${project.id}`}
                        className="block bg-white border border-gray-200 rounded-xl p-6 hover:shadow-md transition-shadow relative group"
                    >
                        {deleteConfirmId === project.id ? (
                            <div className="absolute inset-0 bg-white/95 z-10 flex flex-col items-center justify-center p-4 rounded-xl text-center animate-in fade-in">
                                <AlertTriangle className="text-red-500 mb-2" size={24} />
                                <p className="text-sm font-bold text-gray-900 mb-1">Delete Survey?</p>
                                <p className="text-xs text-gray-500 mb-3">This action cannot be undone.</p>
                                <div className="flex gap-2">
                                    <button
                                        onClick={cancelDelete}
                                        className="px-3 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={confirmDelete}
                                        className="px-3 py-1 text-xs bg-red-600 hover:bg-red-700 rounded text-white"
                                    >
                                        Delete
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <button
                                onClick={(e) => handleDelete(project.id, e)}
                                className="absolute top-4 right-4 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-full opacity-0 group-hover:opacity-100 transition-all"
                                title="Delete Survey"
                            >
                                <Trash2 size={16} />
                            </button>
                        )}

                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                                <Folder size={24} />
                            </div>
                            <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                {project.job_number}
                            </span>
                        </div>

                        <h3 className="text-lg font-bold text-gray-900 mb-1">
                            {project.name}
                        </h3>
                        <p className="text-sm text-gray-500">{project.client}</p>

                        <div className="flex items-center text-blue-600 text-sm font-medium group-hover/link mt-4">
                            View Details
                            <ArrowRight size={16} className="ml-1 group-hover:translate-x-1 transition-transform" />
                        </div>
                    </Link>
                ))}

                {projects?.length === 0 && (
                    <div className="col-span-full text-center py-12 bg-gray-50 rounded-xl border border-dashed border-gray-300">
                        <p className="text-gray-500">No surveys found. Create one to get started.</p>
                    </div>
                )}
            </div>

            <CreateSurveyModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
            />
        </div>
    );
};

export default SurveyList;
