import React, { useState } from 'react';
import { useUsers, useCreateUser, useUpdateUser } from '../../api/hooks';
import type { User, UserCreate, UserUpdate } from '../../api/hooks';
import { Plus, Edit2, Check, X, Shield, User as UserIcon } from 'lucide-react';

const UserManagement = () => {
    const { data: users, isLoading, error } = useUsers();
    const createUser = useCreateUser();
    const updateUser = useUpdateUser();

    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [isEditModalOpen, setIsEditModalOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState<User | null>(null);

    // Form states
    const [formData, setFormData] = useState<UserCreate>({
        username: '',
        email: '',
        full_name: '',
        password: '',
        role: 'Engineer',
        is_active: true,
        is_superuser: false
    });

    const handleAddUser = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await createUser.mutateAsync(formData);
            setIsAddModalOpen(false);
            setFormData({
                username: '',
                email: '',
                full_name: '',
                password: '',
                role: 'Engineer',
                is_active: true,
                is_superuser: false
            });
        } catch (err) {
            console.error("Failed to create user", err);
        }
    };

    const handleUpdateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedUser) return;

        console.log("Updating user:", selectedUser.id);

        try {
            // Only send fields that are relevant for update
            const updates: UserUpdate = {
                role: formData.role,
                is_active: formData.is_active,
                is_superuser: formData.is_superuser
            };

            console.log("Update payload:", updates);

            await updateUser.mutateAsync({ id: selectedUser.id, updates });
            console.log("Update successful");

            setIsEditModalOpen(false);
            setSelectedUser(null);
        } catch (err) {
            console.error("Failed to update user", err);
            alert("Failed to update user. Check console for details.");
        }
    };

    const openEditModal = (user: User) => {
        setSelectedUser(user);
        setFormData({
            ...formData, // Keep other defaults
            role: user.role,
            is_active: user.is_active,
            is_superuser: user.is_superuser
        });
        setIsEditModalOpen(true);
    };

    if (isLoading) return <div className="p-8 text-center text-gray-400">Loading users...</div>;
    if (error) return <div className="p-8 text-center text-red-400">Error loading users</div>;

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-2xl font-bold text-white mb-2">User Management</h1>
                    <p className="text-gray-400">Manage system access and permissions</p>
                </div>
                <button
                    onClick={() => setIsAddModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                >
                    <Plus size={20} />
                    Add User
                </button>
            </div>

            <div className="bg-gray-800 rounded-xl border border-gray-700 overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-gray-900/50 text-gray-400 text-sm uppercase">
                        <tr>
                            <th className="px-6 py-4 font-medium">User</th>
                            <th className="px-6 py-4 font-medium">Role</th>
                            <th className="px-6 py-4 font-medium">Status</th>
                            <th className="px-6 py-4 font-medium">Admin</th>
                            <th className="px-6 py-4 font-medium text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-700">
                        {users?.map((user) => (
                            <tr key={user.id} className="hover:bg-gray-700/30 transition-colors">
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 rounded-full bg-gray-700 flex items-center justify-center text-gray-300">
                                            <UserIcon size={20} />
                                        </div>
                                        <div>
                                            <div className="font-medium text-white">{user.full_name || user.username}</div>
                                            <div className="text-sm text-gray-500">{user.email}</div>
                                        </div>
                                    </div>
                                </td>
                                <td className="px-6 py-4">
                                    <span className="px-3 py-1 rounded-full text-xs font-medium bg-blue-900/30 text-blue-400 border border-blue-800">
                                        {user.role}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    {user.is_active ? (
                                        <span className="flex items-center gap-2 text-green-400 text-sm">
                                            <Check size={16} /> Active
                                        </span>
                                    ) : (
                                        <span className="flex items-center gap-2 text-red-400 text-sm">
                                            <X size={16} /> Inactive
                                        </span>
                                    )}
                                </td>
                                <td className="px-6 py-4">
                                    {user.is_superuser && (
                                        <Shield size={18} className="text-purple-400" />
                                    )}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => openEditModal(user)}
                                        className="p-2 hover:bg-gray-700 rounded-lg text-gray-400 hover:text-white transition-colors"
                                    >
                                        <Edit2 size={18} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            {/* Add User Modal */}
            {isAddModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 w-full max-w-md shadow-xl">
                        <h2 className="text-xl font-bold text-white mb-6">Add New User</h2>
                        <form onSubmit={handleAddUser} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Username (Email)</label>
                                <input
                                    type="email"
                                    required
                                    value={formData.username}
                                    onChange={(e) => setFormData({ ...formData, username: e.target.value, email: e.target.value })}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Full Name</label>
                                <input
                                    type="text"
                                    value={formData.full_name}
                                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Password</label>
                                <input
                                    type="password"
                                    required
                                    value={formData.password}
                                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
                                    <select
                                        value={formData.role}
                                        onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                        className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                    >
                                        <option value="Admin">Admin</option>
                                        <option value="Manager">Manager</option>
                                        <option value="Engineer">Engineer</option>
                                        <option value="Field">Field</option>
                                    </select>
                                </div>
                                <div className="flex items-center gap-2 pt-6">
                                    <input
                                        type="checkbox"
                                        id="is_superuser"
                                        checked={formData.is_superuser}
                                        onChange={(e) => setFormData({ ...formData, is_superuser: e.target.checked })}
                                        className="rounded bg-gray-900 border-gray-700 text-blue-600 focus:ring-blue-500"
                                    />
                                    <label htmlFor="is_superuser" className="text-sm text-gray-400">Superuser</label>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setIsAddModalOpen(false)}
                                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                                >
                                    Create User
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Edit User Modal */}
            {isEditModalOpen && selectedUser && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 w-full max-w-md shadow-xl">
                        <h2 className="text-xl font-bold text-white mb-6">Edit User: {selectedUser.username}</h2>
                        <form onSubmit={handleUpdateUser} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-400 mb-1">Role</label>
                                <select
                                    value={formData.role}
                                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                                    className="w-full bg-gray-900 border border-gray-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-blue-500 outline-none"
                                >
                                    <option value="Admin">Admin</option>
                                    <option value="Manager">Manager</option>
                                    <option value="Engineer">Engineer</option>
                                    <option value="Field">Field</option>
                                </select>
                            </div>

                            <div className="space-y-3">
                                <div className="flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        id="edit_is_active"
                                        checked={formData.is_active}
                                        onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                        className="rounded bg-gray-900 border-gray-700 text-blue-600 focus:ring-blue-500"
                                    />
                                    <label htmlFor="edit_is_active" className="text-sm text-gray-400">Active Account</label>
                                </div>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="checkbox"
                                        id="edit_is_superuser"
                                        checked={formData.is_superuser}
                                        onChange={(e) => setFormData({ ...formData, is_superuser: e.target.checked })}
                                        className="rounded bg-gray-900 border-gray-700 text-blue-600 focus:ring-blue-500"
                                    />
                                    <label htmlFor="edit_is_superuser" className="text-sm text-gray-400">Superuser Access</label>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    type="button"
                                    onClick={() => setIsEditModalOpen(false)}
                                    className="px-4 py-2 text-gray-400 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                                >
                                    Save Changes
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UserManagement;
