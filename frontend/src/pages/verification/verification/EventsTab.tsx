import React, { useState } from 'react';
import { Plus, Trash2, Upload, Calendar, CloudRain, AlertCircle, CheckCircle } from 'lucide-react';
import {
    useVerificationEvents,
    useCreateVerificationEvent,
    useDeleteVerificationEvent,
    usePreviewTraceImport,
    useImportTrace,
} from '../../../api/hooks';
import type {
    VerificationEvent,
    TracePreviewResult
} from '../../../api/hooks';

interface EventsTabProps {
    projectId: number;
}

export default function EventsTab({ projectId }: EventsTabProps) {
    const { data: events, isLoading } = useVerificationEvents(projectId);
    const createEvent = useCreateVerificationEvent();
    const deleteEvent = useDeleteVerificationEvent();
    const previewTrace = usePreviewTraceImport();
    const importTrace = useImportTrace();

    // State for new event form
    const [showNewEventForm, setShowNewEventForm] = useState(false);
    const [newEvent, setNewEvent] = useState({ name: '', event_type: 'STORM', description: '' });

    // State for import wizard
    const [importingEventId, setImportingEventId] = useState<number | null>(null);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewResult, setPreviewResult] = useState<TracePreviewResult | null>(null);
    const [traceName, setTraceName] = useState('');
    const [selectedProfileIndex, setSelectedProfileIndex] = useState(0);

    const handleCreateEvent = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newEvent.name.trim()) return;

        await createEvent.mutateAsync({
            projectId,
            event: newEvent
        });

        setNewEvent({ name: '', event_type: 'STORM', description: '' });
        setShowNewEventForm(false);
    };

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>, eventId: number) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setSelectedFile(file);
        setTraceName(file.name.replace('.csv', ''));
        setImportingEventId(eventId);

        try {
            const result = await previewTrace.mutateAsync({ eventId, file });
            setPreviewResult(result);
        } catch (error) {
            console.error('Preview failed:', error);
        }
    };

    const handleImport = async () => {
        if (!selectedFile || !importingEventId || !traceName) return;

        await importTrace.mutateAsync({
            eventId: importingEventId,
            file: selectedFile,
            traceName,
            profileIndex: selectedProfileIndex,
            projectId
        });

        // Reset state
        setImportingEventId(null);
        setSelectedFile(null);
        setPreviewResult(null);
        setTraceName('');
        setSelectedProfileIndex(0);
    };

    const cancelImport = () => {
        setImportingEventId(null);
        setSelectedFile(null);
        setPreviewResult(null);
        setTraceName('');
        setSelectedProfileIndex(0);
    };

    if (isLoading) {
        return <div className="text-gray-500">Loading events...</div>;
    }

    return (
        <div className="space-y-6">
            {/* New Event Button */}
            {!showNewEventForm && (
                <button
                    onClick={() => setShowNewEventForm(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
                >
                    <Plus size={18} /> Add Event
                </button>
            )}

            {/* New Event Form */}
            {showNewEventForm && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                    <h3 className="font-semibold text-gray-900 mb-4">New Verification Event</h3>
                    <form onSubmit={handleCreateEvent} className="space-y-4">
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Event Name</label>
                                <input
                                    type="text"
                                    value={newEvent.name}
                                    onChange={(e) => setNewEvent({ ...newEvent, name: e.target.value })}
                                    placeholder="e.g., Storm A, DWF Weekday"
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Event Type</label>
                                <select
                                    value={newEvent.event_type}
                                    onChange={(e) => setNewEvent({ ...newEvent, event_type: e.target.value })}
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                                >
                                    <option value="STORM">Storm</option>
                                    <option value="DWF">Dry Weather Flow</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                                <input
                                    type="text"
                                    value={newEvent.description}
                                    onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                                    placeholder="Optional description"
                                    className="w-full border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                                />
                            </div>
                        </div>
                        <div className="flex gap-2">
                            <button
                                type="submit"
                                disabled={createEvent.isPending}
                                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                            >
                                {createEvent.isPending ? 'Creating...' : 'Create Event'}
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowNewEventForm(false)}
                                className="px-4 py-2 text-gray-600 hover:text-gray-900"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Events List */}
            {events && events.length > 0 ? (
                <div className="space-y-4">
                    {events.map((event: VerificationEvent) => (
                        <div key={event.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-sm transition-shadow">
                            <div className="flex items-start justify-between">
                                <div className="flex items-center gap-3">
                                    {event.event_type === 'STORM' ? (
                                        <CloudRain className="text-blue-500" size={24} />
                                    ) : (
                                        <Calendar className="text-amber-500" size={24} />
                                    )}
                                    <div>
                                        <h3 className="font-semibold text-gray-900">{event.name}</h3>
                                        <p className="text-sm text-gray-500">
                                            {event.event_type} • Created {new Date(event.created_at).toLocaleDateString()}
                                        </p>
                                        {event.description && (
                                            <p className="text-sm text-gray-600 mt-1">{event.description}</p>
                                        )}
                                    </div>
                                </div>
                                <div className="flex items-center gap-2">
                                    <label className="flex items-center gap-2 px-3 py-1.5 bg-green-50 text-green-700 rounded-md hover:bg-green-100 cursor-pointer text-sm">
                                        <Upload size={16} />
                                        Import Traces
                                        <input
                                            type="file"
                                            accept=".csv"
                                            className="hidden"
                                            onChange={(e) => handleFileSelect(e, event.id)}
                                        />
                                    </label>
                                    <button
                                        onClick={() => deleteEvent.mutate({ eventId: event.id, projectId })}
                                        className="p-1.5 text-red-500 hover:bg-red-50 rounded"
                                        title="Delete Event"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            </div>

                            {/* Import Preview for this event */}
                            {importingEventId === event.id && previewResult && (
                                <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
                                    <h4 className="font-medium text-gray-900 mb-3">Import Preview: {selectedFile?.name}</h4>

                                    {previewResult.errors.length > 0 && (
                                        <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded-md">
                                            <div className="flex items-center gap-2 text-red-700 font-medium">
                                                <AlertCircle size={16} /> Errors
                                            </div>
                                            <ul className="text-sm text-red-600 mt-1">
                                                {previewResult.errors.map((err, i) => <li key={i}>{err}</li>)}
                                            </ul>
                                        </div>
                                    )}

                                    {previewResult.monitors_found.length > 0 && (
                                        <>
                                            <div className="mb-3">
                                                <label className="block text-sm font-medium text-gray-700 mb-1">Trace Set Name</label>
                                                <input
                                                    type="text"
                                                    value={traceName}
                                                    onChange={(e) => setTraceName(e.target.value)}
                                                    className="w-full max-w-xs border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                                                />
                                            </div>

                                            {previewResult.predicted_profiles.length > 1 && (
                                                <div className="mb-3">
                                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                                        Select Predicted Profile ({previewResult.predicted_profiles.length} found)
                                                    </label>
                                                    <select
                                                        value={selectedProfileIndex}
                                                        onChange={(e) => setSelectedProfileIndex(Number(e.target.value))}
                                                        className="w-full max-w-xs border-gray-300 rounded-md shadow-sm focus:ring-green-500 focus:border-green-500"
                                                    >
                                                        {previewResult.predicted_profiles.map((profile, i) => (
                                                            <option key={i} value={i}>{profile}</option>
                                                        ))}
                                                    </select>
                                                </div>
                                            )}

                                            <div className="mb-3">
                                                <p className="text-sm font-medium text-gray-700 mb-2">
                                                    Monitors found: {previewResult.monitors_found.length}
                                                </p>
                                                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-sm">
                                                    {previewResult.monitors_found.map((m) => (
                                                        <div key={m.page_index} className="flex items-center gap-2 text-gray-600">
                                                            <CheckCircle size={14} className="text-green-500" />
                                                            {m.obs_location} → {m.pred_location} ({m.record_count} records)
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>

                                            <div className="flex gap-2">
                                                <button
                                                    onClick={handleImport}
                                                    disabled={importTrace.isPending}
                                                    className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                                                >
                                                    {importTrace.isPending ? 'Importing...' : 'Import'}
                                                </button>
                                                <button
                                                    onClick={cancelImport}
                                                    className="px-4 py-2 text-gray-600 hover:text-gray-900"
                                                >
                                                    Cancel
                                                </button>
                                            </div>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            ) : (
                <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                    <Calendar className="mx-auto text-gray-400 mb-3" size={48} />
                    <p className="text-gray-500 mb-2">No events defined yet</p>
                    <p className="text-sm text-gray-400">Create an event to start importing verification traces.</p>
                </div>
            )}
        </div>
    );
}
