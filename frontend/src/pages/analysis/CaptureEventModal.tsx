import React, { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { format } from 'date-fns';

interface EventResult {
    event_id: number;
    dataset_id: number;
    dataset_name: string;
    start_time: string;
    end_time: string;
    total_mm: number;
    duration_hours: number;
    peak_intensity: number;
    status: string;
    passed: number;
}

interface DryDayResult {
    dataset_id: number;
    dataset_name: string;
    date: string;
    total_mm: number;
}

interface CaptureEventModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSave: (eventData: {
        name: string;
        event_type: string;
        start_time: string;
        end_time: string;
    }) => Promise<void>;
    sourceEvent?: EventResult | null;
    sourceDryDay?: DryDayResult | null;
    projectId: number;
}

const CaptureEventModal: React.FC<CaptureEventModalProps> = ({
    isOpen,
    onClose,
    onSave,
    sourceEvent,
    sourceDryDay,
    projectId
}) => {
    const [eventName, setEventName] = useState('');
    const [eventType, setEventType] = useState<'Storm Event' | 'Dry Day' | 'Dry Period'>('Storm Event');
    const [startTime, setStartTime] = useState('');
    const [endTime, setEndTime] = useState('');
    const [isSaving, setIsSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Pre-fill form when modal opens
    useEffect(() => {
        if (isOpen) {
            if (sourceEvent) {
                // Capturing from detected event
                setEventName(`${sourceEvent.dataset_name} - ${sourceEvent.status}`);
                setEventType('Storm Event');
                setStartTime(format(new Date(sourceEvent.start_time), "yyyy-MM-dd'T'HH:mm"));
                setEndTime(format(new Date(sourceEvent.end_time), "yyyy-MM-dd'T'HH:mm"));
            } else if (sourceDryDay) {
                // Capturing from dry day
                setEventName(`${sourceDryDay.dataset_name} - Dry Day`);
                setEventType('Dry Day');
                const dayStart = new Date(sourceDryDay.date);
                const dayEnd = new Date(sourceDryDay.date);
                dayEnd.setHours(23, 59, 59);
                setStartTime(format(dayStart, "yyyy-MM-dd'T'HH:mm"));
                setEndTime(format(dayEnd, "yyyy-MM-dd'T'HH:mm"));
            } else {
                // Manual event creation
                setEventName('');
                setEventType('Storm Event');
                setStartTime('');
                setEndTime('');
            }
            setError(null);
        }
    }, [isOpen, sourceEvent, sourceDryDay]);

    const handleSave = async () => {
        // Validation
        if (!eventName.trim()) {
            setError('Event name is required');
            return;
        }
        if (!startTime || !endTime) {
            setError('Start and end times are required');
            return;
        }
        if (new Date(endTime) <= new Date(startTime)) {
            setError('End time must be after start time');
            return;
        }

        setIsSaving(true);
        setError(null);

        try {
            await onSave({
                name: eventName,
                event_type: eventType,
                start_time: new Date(startTime).toISOString(),
                end_time: new Date(endTime).toISOString()
            });
            onClose();
        } catch (err: any) {
            setError(err.message || 'Failed to save event');
        } finally {
            setIsSaving(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-gray-200">
                    <h2 className="text-xl font-semibold text-gray-900">
                        {sourceEvent || sourceDryDay ? 'Capture Event' : 'Add Event'}
                    </h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Body */}
                <div className="p-6 space-y-4">
                    {/* Event Name */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Event Name *
                        </label>
                        <input
                            type="text"
                            value={eventName}
                            onChange={(e) => setEventName(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                            placeholder="e.g., Storm Event 2024-01-15"
                        />
                    </div>

                    {/* Event Type */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Event Type *
                        </label>
                        <select
                            value={eventType}
                            onChange={(e) => setEventType(e.target.value as any)}
                            disabled={!!(sourceEvent || sourceDryDay)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
                        >
                            <option value="Storm Event">Storm Event</option>
                            <option value="Dry Day">Dry Day</option>
                            <option value="Dry Period">Dry Period</option>
                        </select>
                        {(sourceEvent || sourceDryDay) && (
                            <p className="text-xs text-gray-500 mt-1">
                                Event type is pre-filled based on source
                            </p>
                        )}
                    </div>

                    {/* Start Time */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            Start Time *
                        </label>
                        <input
                            type="datetime-local"
                            value={startTime}
                            onChange={(e) => setStartTime(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                    </div>

                    {/* End Time */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                            End Time *
                        </label>
                        <input
                            type="datetime-local"
                            value={endTime}
                            onChange={(e) => setEndTime(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                        />
                    </div>

                    {/* Read-only metadata for captured events */}
                    {sourceEvent && (
                        <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
                            <h4 className="text-sm font-semibold text-gray-700 mb-2">Event Details</h4>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                    <span className="text-gray-600">Dataset:</span>
                                    <span className="ml-2 font-medium">{sourceEvent.dataset_name}</span>
                                </div>
                                <div>
                                    <span className="text-gray-600">Status:</span>
                                    <span className="ml-2 font-medium">{sourceEvent.status}</span>
                                </div>
                                <div>
                                    <span className="text-gray-600">Total Rainfall:</span>
                                    <span className="ml-2 font-medium">{sourceEvent.total_mm} mm</span>
                                </div>
                                <div>
                                    <span className="text-gray-600">Duration:</span>
                                    <span className="ml-2 font-medium">{sourceEvent.duration_hours} hrs</span>
                                </div>
                                <div>
                                    <span className="text-gray-600">Peak Intensity:</span>
                                    <span className="ml-2 font-medium">{sourceEvent.peak_intensity} mm/hr</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {sourceDryDay && (
                        <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
                            <h4 className="text-sm font-semibold text-gray-700 mb-2">Dry Day Details</h4>
                            <div className="grid grid-cols-2 gap-2 text-sm">
                                <div>
                                    <span className="text-gray-600">Dataset:</span>
                                    <span className="ml-2 font-medium">{sourceDryDay.dataset_name}</span>
                                </div>
                                <div>
                                    <span className="text-gray-600">Total Rainfall:</span>
                                    <span className="ml-2 font-medium">{sourceDryDay.total_mm} mm</span>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Error Message */}
                    {error && (
                        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
                            {error}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-end gap-3 p-6 border-t border-gray-200 bg-gray-50">
                    <button
                        onClick={onClose}
                        disabled={isSaving}
                        className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={isSaving}
                        className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center"
                    >
                        {isSaving ? 'Saving...' : 'Save Event'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CaptureEventModal;
