import React, { useState, useRef, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
    useProjects, useImportProjectCsv, useDeleteProject, useUpdateProject,
    useProjectCollaborators, useAddCollaborator, useRemoveCollaborator,
    useCurrentUser
} from '../../api/hooks';
import { ClipboardList, ArrowRight, Loader2, Upload, Trash2, Pencil, Info, AlertTriangle, X, Settings, Users } from 'lucide-react';
import CreateSurveyModal from './CreateSurveyModal';
import CollaboratorsPanel from '../../components/CollaboratorsPanel';

const SurveyList: React.FC = () => {
    const { data: projects, isLoading, error } = useProjects();
    const { mutate: importCsv, isPending: isImporting } = useImportProjectCsv();
    const { mutate: deleteProject } = useDeleteProject();
    const updateProject = useUpdateProject();
    const { data: currentUser } = useCurrentUser();

    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);
    const [editingProject, setEditingProject] = useState<any>(null);
    const [activeTab, setActiveTab] = useState<'general' | 'collaborators'>('general');
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Form state for editing
    const [formData, setFormData] = useState({
        name: '',
        client: '',
        job_number: '',
        client_job_ref: ''
    });

    // Collaborator hooks
    const { data: collaborators, isLoading: loadingCollabs } = useProjectCollaborators(editingProject?.id || 0);
    const addCollaborator = useAddCollaborator();
    const removeCollaborator = useRemoveCollaborator();

    const isOwner = currentUser?.is_superuser || currentUser?.role === 'Admin' ||
        editingProject?.owner_id === currentUser?.id;

    // Update form when editing project changes
    useEffect(() => {
        if (editingProject) {
            setFormData({
                name: editingProject.name || '',
                client: editingProject.client || '',
                job_number: editingProject.job_number || '',
                client_job_ref: editingProject.client_job_ref || ''
            });
        }
    }, [editingProject]);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            importCsv(e.target.files[0]);
            e.target.value = '';
        }
    };

    const handleDelete = (id: number, e: React.MouseEvent) => {
        e.preventDefault();
        setDeleteConfirmId(id);
    };

    const handleEditClick = (e: React.MouseEvent, project: any) => {
        e.preventDefault();
        e.stopPropagation();
        setEditingProject(project);
        setActiveTab('general');
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

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (!editingProject) return;

        updateProject.mutate({ id: editingProject.id, updates: formData }, {
            onSuccess: () => {
                setEditingProject(null);
            }
        });
    };

    const handleAddCollaborator = async (username: string) => {
        if (!editingProject?.id) return;
        await addCollaborator.mutateAsync({ projectId: editingProject.id, usernameOrEmail: username });
    };

    const handleRemoveCollaborator = (userId: number) => {
        if (!editingProject?.id) return;
        removeCollaborator.mutate({ projectId: editingProject.id, userId });
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
                    <h1 className="text-2xl font-bold text-gray-900">Flow Surveys</h1>
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
                        ) : null}

                        <div className="flex items-start justify-between mb-4">
                            <div className="p-3 bg-blue-50 text-blue-600 rounded-lg">
                                <ClipboardList size={24} />
                            </div>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-medium bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                                    {project.job_number}
                                </span>
                                {deleteConfirmId !== project.id && (
                                    <>
                                        <button
                                            onClick={(e) => handleEditClick(e, project)}
                                            className="p-1 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition"
                                            title="Edit Survey"
                                        >
                                            <Pencil size={16} />
                                        </button>
                                        <button
                                            onClick={(e) => handleDelete(project.id, e)}
                                            className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded transition"
                                            title="Delete Survey"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </>
                                )}
                            </div>
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

            {/* Edit Project Modal with Settings + Collaborators tabs */}
            {editingProject && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-lg w-full p-6 shadow-xl max-h-[90vh] flex flex-col">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-gray-900">
                                Edit Survey
                            </h2>
                            <button
                                onClick={() => setEditingProject(null)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <X size={20} className="text-gray-500" />
                            </button>
                        </div>

                        {/* Tabs */}
                        <div className="flex border-b border-gray-200 mb-6">
                            <button
                                onClick={() => setActiveTab('general')}
                                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'general'
                                    ? 'border-blue-600 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                <Settings size={16} />
                                General
                            </button>
                            <button
                                onClick={() => setActiveTab('collaborators')}
                                className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors flex items-center gap-2 ${activeTab === 'collaborators'
                                    ? 'border-blue-600 text-blue-600'
                                    : 'border-transparent text-gray-500 hover:text-gray-700'
                                    }`}
                            >
                                <Users size={16} />
                                Collaborators
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto">
                            {activeTab === 'general' ? (
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Survey Name</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Client</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                                            value={formData.client}
                                            onChange={(e) => setFormData({ ...formData, client: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Job Number</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                                            value={formData.job_number}
                                            onChange={(e) => setFormData({ ...formData, job_number: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Client Job Ref (optional)</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition"
                                            value={formData.client_job_ref}
                                            onChange={(e) => setFormData({ ...formData, client_job_ref: e.target.value })}
                                        />
                                    </div>
                                    <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                        <button
                                            type="button"
                                            onClick={() => setEditingProject(null)}
                                            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                                        >
                                            Cancel
                                        </button>
                                        <button
                                            type="submit"
                                            disabled={updateProject.isPending}
                                            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center"
                                        >
                                            {updateProject.isPending && <Loader2 className="animate-spin mr-2" size={16} />}
                                            Save Changes
                                        </button>
                                    </div>
                                </form>
                            ) : (
                                <CollaboratorsPanel
                                    collaborators={collaborators}
                                    isLoading={loadingCollabs}
                                    isOwner={isOwner ?? false}
                                    onAdd={handleAddCollaborator}
                                    onRemove={handleRemoveCollaborator}
                                    isAdding={addCollaborator.isPending}
                                    accentColor="blue"
                                />
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default SurveyList;
