import React, { useState } from 'react';
import { Users, Loader2, Trash2, UserPlus } from 'lucide-react';
import type { User } from '../api/hooks';

interface CollaboratorsPanelProps {
    collaborators: User[] | undefined;
    isLoading: boolean;
    isOwner: boolean;
    onAdd: (username: string) => Promise<void>;
    onRemove: (userId: number) => void;
    isAdding?: boolean;
    accentColor?: string;
}

const CollaboratorsPanel: React.FC<CollaboratorsPanelProps> = ({
    collaborators,
    isLoading,
    isOwner,
    onAdd,
    onRemove,
    isAdding = false,
    accentColor = 'blue'
}) => {
    const [newUsername, setNewUsername] = useState('');
    const [addError, setAddError] = useState('');

    const handleAdd = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newUsername.trim()) return;

        setAddError('');
        try {
            await onAdd(newUsername.trim());
            setNewUsername('');
        } catch {
            setAddError('Failed to add collaborator. User may not exist.');
        }
    };

    const colorClasses = {
        blue: {
            bg: 'bg-blue-50',
            text: 'text-blue-600',
            textDark: 'text-blue-900',
            textMedium: 'text-blue-700',
            avatar: 'bg-blue-100 text-blue-600',
        },
        purple: {
            bg: 'bg-purple-50',
            text: 'text-purple-600',
            textDark: 'text-purple-900',
            textMedium: 'text-purple-700',
            avatar: 'bg-purple-100 text-purple-600',
        },
        green: {
            bg: 'bg-green-50',
            text: 'text-green-600',
            textDark: 'text-green-900',
            textMedium: 'text-green-700',
            avatar: 'bg-green-100 text-green-600',
        },
        amber: {
            bg: 'bg-amber-50',
            text: 'text-amber-600',
            textDark: 'text-amber-900',
            textMedium: 'text-amber-700',
            avatar: 'bg-amber-100 text-amber-600',
        },
    };

    const colors = colorClasses[accentColor as keyof typeof colorClasses] || colorClasses.blue;

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className={`${colors.bg} p-4 rounded-lg flex items-start gap-3`}>
                <Users className={`${colors.text} mt-1`} size={20} />
                <div>
                    <h3 className={`text-sm font-semibold ${colors.textDark}`}>Manage Access</h3>
                    <p className={`text-sm ${colors.textMedium}`}>
                        Collaborators can view and edit this project, but cannot delete it.
                    </p>
                </div>
            </div>

            {/* Add Collaborator Form */}
            {isOwner && (
                <form onSubmit={handleAdd} className="space-y-2">
                    <div className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Enter username"
                            value={newUsername}
                            onChange={(e) => setNewUsername(e.target.value)}
                            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <button
                            type="submit"
                            disabled={isAdding || !newUsername.trim()}
                            className="px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors flex items-center gap-2 whitespace-nowrap disabled:opacity-50"
                        >
                            {isAdding ? <Loader2 size={16} className="animate-spin" /> : <UserPlus size={16} />}
                            Add
                        </button>
                    </div>
                    {addError && (
                        <p className="text-red-500 text-sm">{addError}</p>
                    )}
                </form>
            )}

            {/* Collaborators List */}
            <div className="space-y-2">
                <h3 className="text-sm font-medium text-gray-700">Current Collaborators</h3>
                {isLoading ? (
                    <div className="text-center py-4 text-gray-500">
                        <Loader2 size={20} className="animate-spin mx-auto" />
                    </div>
                ) : collaborators?.length === 0 ? (
                    <div className="text-center py-8 text-gray-500 bg-gray-50 rounded-lg border border-dashed border-gray-300">
                        No collaborators yet
                    </div>
                ) : (
                    <div className="space-y-2">
                        {collaborators?.map(user => (
                            <div
                                key={user.id}
                                className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg shadow-sm"
                            >
                                <div className="flex items-center gap-3">
                                    <div className={`w-8 h-8 rounded-full ${colors.avatar} flex items-center justify-center font-bold text-sm`}>
                                        {user.username.substring(0, 2).toUpperCase()}
                                    </div>
                                    <div>
                                        <div className="text-sm font-medium text-gray-900">
                                            {user.full_name || user.username}
                                        </div>
                                        <div className="text-xs text-gray-500">
                                            {user.email || user.username}
                                        </div>
                                    </div>
                                </div>
                                {isOwner && (
                                    <button
                                        onClick={() => onRemove(user.id)}
                                        className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                                        title="Remove Access"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default CollaboratorsPanel;
