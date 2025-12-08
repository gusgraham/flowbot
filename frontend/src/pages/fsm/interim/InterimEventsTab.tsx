import React, { useState } from 'react';
import {
    useFsmProjectEvents,
    useDetectEvents,
    useUpdateEvent,
    useDeleteEvent
} from '../../../api/hooks';
import type { FsmEvent } from '../../../api/hooks';
import { format } from 'date-fns';
import { useToast } from '../../../contexts/ToastContext';

interface InterimEventsTabProps {
    projectId: number;
    startDate: string;
    endDate: string;
}

const InterimEventsTab: React.FC<InterimEventsTabProps> = ({ projectId, startDate, endDate }) => {
    const [isParamsOpen, setIsParamsOpen] = useState(false);
    const [minIntensity, setMinIntensity] = useState(0.5);
    const [minDurationHours, setMinDurationHours] = useState(0.5);
    const [precedingDryHours, setPrecedingDryHours] = useState(6.0);

    const { data: events, isLoading, refetch } = useFsmProjectEvents(projectId, startDate, endDate);
    const detectEvents = useDetectEvents();
    const updateEvent = useUpdateEvent();
    const deleteEvent = useDeleteEvent();
    const toast = useToast();

    const handleDetectEvents = async () => {
        try {
            await detectEvents.mutateAsync({
                projectId,
                startDate,
                endDate,
                minIntensity,
                minDurationHours,
                precedingDryHours,
            });
            toast.success('Events detected successfully');
            refetch();
        } catch (error) {
            toast.error('Failed to detect events');
        }
    };

    const handleToggleReviewed = async (event: FsmEvent) => {
        try {
            await updateEvent.mutateAsync({
                eventId: event.id,
                reviewed: !event.reviewed,
            });
        } catch (error) {
            toast.error('Failed to update event');
        }
    };

    const handleUpdateComment = async (eventId: number, comment: string) => {
        try {
            await updateEvent.mutateAsync({
                eventId,
                review_comment: comment,
            });
        } catch (error) {
            toast.error('Failed to update comment');
        }
    };

    const handleDeleteEvent = async (eventId: number) => {
        if (!confirm('Are you sure you want to delete this event?')) return;
        try {
            await deleteEvent.mutateAsync(eventId);
            toast.success('Event deleted');
        } catch (error) {
            toast.error('Failed to delete event');
        }
    };

    const formatDateTime = (dateStr: string) => {
        try {
            return format(new Date(dateStr), 'dd MMM yyyy HH:mm');
        } catch {
            return dateStr;
        }
    };

    const stormEvents = events?.filter(e => e.event_type === 'Storm') || [];
    const otherEvents = events?.filter(e => e.event_type !== 'Storm') || [];

    return (
        <div style={{ padding: '24px' }}>
            {/* Parameters Section */}
            <div style={{
                backgroundColor: 'var(--color-bg-secondary, #1a1a2e)',
                borderRadius: '12px',
                padding: '16px',
                marginBottom: '24px',
            }}>
                <div
                    style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        cursor: 'pointer',
                    }}
                    onClick={() => setIsParamsOpen(!isParamsOpen)}
                >
                    <h3 style={{ margin: 0, fontSize: '14px', color: 'var(--color-text-secondary, #a0a0a0)' }}>
                        Detection Parameters
                    </h3>
                    <span style={{ color: 'var(--color-text-secondary, #a0a0a0)' }}>
                        {isParamsOpen ? '▲' : '▼'}
                    </span>
                </div>

                {isParamsOpen && (
                    <div style={{
                        marginTop: '16px',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(3, 1fr)',
                        gap: '16px'
                    }}>
                        <div>
                            <label style={{ fontSize: '12px', color: 'var(--color-text-secondary, #a0a0a0)', display: 'block', marginBottom: '4px' }}>
                                Min Intensity (mm/hr)
                            </label>
                            <input
                                type="number"
                                step="0.1"
                                value={minIntensity}
                                onChange={(e) => setMinIntensity(parseFloat(e.target.value))}
                                style={{
                                    width: '100%',
                                    padding: '8px',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-border, #333)',
                                    backgroundColor: 'var(--color-bg-primary, #0f0f1a)',
                                    color: 'var(--color-text-primary, #fff)',
                                }}
                            />
                        </div>
                        <div>
                            <label style={{ fontSize: '12px', color: 'var(--color-text-secondary, #a0a0a0)', display: 'block', marginBottom: '4px' }}>
                                Min Duration (hours)
                            </label>
                            <input
                                type="number"
                                step="0.5"
                                value={minDurationHours}
                                onChange={(e) => setMinDurationHours(parseFloat(e.target.value))}
                                style={{
                                    width: '100%',
                                    padding: '8px',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-border, #333)',
                                    backgroundColor: 'var(--color-bg-primary, #0f0f1a)',
                                    color: 'var(--color-text-primary, #fff)',
                                }}
                            />
                        </div>
                        <div>
                            <label style={{ fontSize: '12px', color: 'var(--color-text-secondary, #a0a0a0)', display: 'block', marginBottom: '4px' }}>
                                Preceding Dry Period (hours)
                            </label>
                            <input
                                type="number"
                                step="1"
                                value={precedingDryHours}
                                onChange={(e) => setPrecedingDryHours(parseFloat(e.target.value))}
                                style={{
                                    width: '100%',
                                    padding: '8px',
                                    borderRadius: '6px',
                                    border: '1px solid var(--color-border, #333)',
                                    backgroundColor: 'var(--color-bg-primary, #0f0f1a)',
                                    color: 'var(--color-text-primary, #fff)',
                                }}
                            />
                        </div>
                    </div>
                )}

                <div style={{ marginTop: '16px', display: 'flex', gap: '12px' }}>
                    <button
                        onClick={handleDetectEvents}
                        disabled={detectEvents.isPending}
                        style={{
                            padding: '10px 20px',
                            borderRadius: '8px',
                            border: 'none',
                            backgroundColor: 'var(--color-primary, #6366f1)',
                            color: 'white',
                            cursor: detectEvents.isPending ? 'not-allowed' : 'pointer',
                            opacity: detectEvents.isPending ? 0.7 : 1,
                            fontWeight: 500,
                        }}
                    >
                        {detectEvents.isPending ? 'Detecting...' : '🔍 Detect Events'}
                    </button>
                </div>
            </div>

            {/* Events List */}
            {isLoading ? (
                <div style={{ textAlign: 'center', padding: '40px', color: 'var(--color-text-secondary, #a0a0a0)' }}>
                    Loading events...
                </div>
            ) : (
                <>
                    {/* Storm Events */}
                    <div style={{ marginBottom: '24px' }}>
                        <h3 style={{
                            fontSize: '16px',
                            marginBottom: '12px',
                            color: 'var(--color-text-primary, #fff)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                        }}>
                            ⛈️ Storm Events ({stormEvents.length})
                        </h3>

                        {stormEvents.length === 0 ? (
                            <div style={{
                                padding: '20px',
                                textAlign: 'center',
                                color: 'var(--color-text-secondary, #a0a0a0)',
                                backgroundColor: 'var(--color-bg-secondary, #1a1a2e)',
                                borderRadius: '8px',
                            }}>
                                No storm events detected
                            </div>
                        ) : (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {stormEvents.map((event) => (
                                    <EventCard
                                        key={event.id}
                                        event={event}
                                        formatDateTime={formatDateTime}
                                        onToggleReviewed={handleToggleReviewed}
                                        onUpdateComment={handleUpdateComment}
                                        onDelete={handleDeleteEvent}
                                    />
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Other Events */}
                    {otherEvents.length > 0 && (
                        <div>
                            <h3 style={{
                                fontSize: '16px',
                                marginBottom: '12px',
                                color: 'var(--color-text-primary, #fff)',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px',
                            }}>
                                📋 Other Events ({otherEvents.length})
                            </h3>

                            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                                {otherEvents.map((event) => (
                                    <EventCard
                                        key={event.id}
                                        event={event}
                                        formatDateTime={formatDateTime}
                                        onToggleReviewed={handleToggleReviewed}
                                        onUpdateComment={handleUpdateComment}
                                        onDelete={handleDeleteEvent}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

interface EventCardProps {
    event: FsmEvent;
    formatDateTime: (dateStr: string) => string;
    onToggleReviewed: (event: FsmEvent) => void;
    onUpdateComment: (eventId: number, comment: string) => void;
    onDelete: (eventId: number) => void;
}

const EventCard: React.FC<EventCardProps> = ({ event, formatDateTime, onToggleReviewed, onUpdateComment, onDelete }) => {
    const [isExpanded, setIsExpanded] = useState(false);
    const [comment, setComment] = useState(event.review_comment || '');

    const getEventColor = (type: string) => {
        switch (type) {
            case 'Storm': return '#3b82f6';
            case 'No Event': return '#6b7280';
            case 'Dry Day': return '#f59e0b';
            default: return '#6b7280';
        }
    };

    return (
        <div style={{
            backgroundColor: 'var(--color-bg-secondary, #1a1a2e)',
            borderRadius: '8px',
            padding: '12px 16px',
            borderLeft: `4px solid ${getEventColor(event.event_type)}`,
        }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                    <input
                        type="checkbox"
                        checked={event.reviewed}
                        onChange={() => onToggleReviewed(event)}
                        style={{ width: '18px', height: '18px', cursor: 'pointer' }}
                        title="Mark as reviewed"
                    />
                    <div>
                        <div style={{ fontWeight: 500, color: 'var(--color-text-primary, #fff)' }}>
                            {formatDateTime(event.start_time)} - {formatDateTime(event.end_time)}
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--color-text-secondary, #a0a0a0)', marginTop: '2px' }}>
                            {event.total_rainfall_mm?.toFixed(1)} mm total •
                            {event.max_intensity_mm_hr?.toFixed(1)} mm/hr max •
                            {event.event_type}
                        </div>
                    </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {event.reviewed && (
                        <span style={{
                            fontSize: '12px',
                            color: '#22c55e',
                            backgroundColor: 'rgba(34, 197, 94, 0.1)',
                            padding: '2px 8px',
                            borderRadius: '4px',
                        }}>
                            ✓ Reviewed
                        </span>
                    )}
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: 'var(--color-text-secondary, #a0a0a0)',
                            cursor: 'pointer',
                            fontSize: '12px',
                        }}
                    >
                        {isExpanded ? '▲' : '▼'}
                    </button>
                    <button
                        onClick={() => onDelete(event.id)}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: '#ef4444',
                            cursor: 'pointer',
                            fontSize: '16px',
                        }}
                        title="Delete event"
                    >
                        🗑️
                    </button>
                </div>
            </div>

            {isExpanded && (
                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--color-border, #333)' }}>
                    <label style={{ fontSize: '12px', color: 'var(--color-text-secondary, #a0a0a0)', display: 'block', marginBottom: '4px' }}>
                        Comments
                    </label>
                    <textarea
                        value={comment}
                        onChange={(e) => setComment(e.target.value)}
                        onBlur={() => onUpdateComment(event.id, comment)}
                        placeholder="Add review notes..."
                        style={{
                            width: '100%',
                            padding: '8px',
                            borderRadius: '6px',
                            border: '1px solid var(--color-border, #333)',
                            backgroundColor: 'var(--color-bg-primary, #0f0f1a)',
                            color: 'var(--color-text-primary, #fff)',
                            minHeight: '60px',
                            resize: 'vertical',
                        }}
                    />
                </div>
            )}
        </div>
    );
};

export default InterimEventsTab;
