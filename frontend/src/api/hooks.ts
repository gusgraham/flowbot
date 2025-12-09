import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './client';

// Types
export interface Project {
    id: number;
    name: string;
    client: string;
    job_number: string;
    client_job_ref?: string;
    survey_start_date?: string;
    survey_end_date?: string;
    owner_id?: number;
    created_at?: string;
    default_download_path?: string;
    last_ingestion_date?: string;
}

export interface Site {
    id: number;
    project_id: number;
    name: string;
    catchment: string;
    site_id: string;
    site_type: string;
    address?: string;
    mh_ref?: string;
    w3w?: string;
    easting: number;
    northing: number;
}

export interface Monitor {
    id: number;
    monitor_asset_id: string;
    monitor_type: string;
    monitor_sub_type: string;
    pmac_id?: string;
    project_id?: number;
}

export interface Install {
    id: number;
    monitor_id: number;
    install_date: string;
    removal_date?: string;
    height?: number;
    install_id: string;
    install_type: string;
    project_id: number;
    site_id: number;
    // FM Specific
    fm_pipe_shape?: string;
    fm_pipe_height_mm?: number;
    fm_pipe_width_mm?: number;
    fm_pipe_letter?: string;
    fm_pipe_depth_to_invert_mm?: number;
    fm_sensor_offset_mm?: number;
    // RG Specific
    rg_position?: string;

    // Status
    last_data_ingested?: string;
    last_data_processed?: string;
}

export interface Visit {
    id: number;
    install_id: number;
    date: string;
    crew: string;
    stage_time?: string;
    stage_depth?: number;
}

export interface RainfallEvent {
    id: number;
    monitor_id: number;
    start_time: string;
    end_time: string;
    total_depth: number;
    peak_intensity: number;
}

export interface ScatterData {
    flow: number;
    depth: number;
    velocity: number;
    time: string;
}

export interface WQData {
    time: string;
    parameter: string;
    value: number;
}

// Analysis Projects
export interface AnalysisProject {
    id: number;
    name: string;
    client: string;
    job_number: string;
    description?: string;
    created_at: string;
}

export interface AnalysisProjectCreate {
    name: string;
    client: string;
    job_number: string;
    description?: string;
}

export const useAnalysisProjects = () => {
    return useQuery({
        queryKey: ['analysis_projects'],
        queryFn: async () => {
            const { data } = await api.get<AnalysisProject[]>('/fsa/projects');
            return data;
        },
    });
};

export const useAnalysisProject = (id: number) => {
    return useQuery({
        queryKey: ['analysis_projects', id],
        queryFn: async () => {
            const { data } = await api.get<AnalysisProject>(`/fsa/projects/${id}`);
            return data;
        },
        enabled: !!id,
    });
};

export const useCreateAnalysisProject = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (newProject: AnalysisProjectCreate) => {
            const { data } = await api.post<AnalysisProject>('/fsa/projects', newProject);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['analysis_projects'] });
        },
    });
};

// Verification Projects
export interface VerificationProject {
    id: number;
    name: string;
    client: string;
    job_number: string;
    model_name?: string;
    description?: string;
    created_at: string;
}

export interface VerificationProjectCreate {
    name: string;
    client: string;
    job_number: string;
    model_name?: string;
    description?: string;
}

export const useVerificationProjects = () => {
    return useQuery({
        queryKey: ['verification_projects'],
        queryFn: async () => {
            const { data } = await api.get<VerificationProject[]>('/verification/projects');
            return data;
        },
    });
};

export const useCreateVerificationProject = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (newProject: VerificationProjectCreate) => {
            const { data } = await api.post<VerificationProject>('/verification/projects', newProject);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['verification_projects'] });
        },
    });
};

// Water Quality Projects
export interface WaterQualityProject {
    id: number;
    name: string;
    client: string;
    job_number: string;
    campaign_date?: string;
    description?: string;
    created_at: string;
}

export interface WaterQualityProjectCreate {
    name: string;
    client: string;
    job_number: string;
    campaign_date?: string;
    description?: string;
}

export const useWQProjects = () => {
    return useQuery({
        queryKey: ['wq_projects'],
        queryFn: async () => {
            const { data } = await api.get<WaterQualityProject[]>('/wq/projects');
            return data;
        },
    });
};

export const useCreateWQProject = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (newProject: WaterQualityProjectCreate) => {
            const { data } = await api.post<WaterQualityProject>('/wq/projects', newProject);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['wq_projects'] });
        },
    });
};

// Projects (FSM)
export const useProjects = () => {
    return useQuery({
        queryKey: ['projects'],
        queryFn: async () => {
            const { data } = await api.get<Project[]>('/projects');
            return data;
        },
    });
};

export interface ProjectCreate {
    name: string;
    job_number: string;
    client: string;
    client_job_ref?: string;
    description?: string;
    survey_start_date?: string;
    survey_end_date?: string;
    default_download_path?: string;
}

export const useCreateProject = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (newProject: ProjectCreate) => {
            const { data } = await api.post<Project>('/projects', newProject);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
        },
    });
};

export const useUpdateProject = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ id, updates }: { id: number; updates: ProjectCreate }) => {
            const { data } = await api.put<Project>(`/projects/${id}`, updates);
            return data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
            queryClient.invalidateQueries({ queryKey: ['projects', data.id] });
        },
    });
};

// Collaborators
export const useProjectCollaborators = (projectId: number) => {
    return useQuery({
        queryKey: ['project_collaborators', projectId],
        queryFn: async () => {
            const { data } = await api.get<User[]>(`/projects/${projectId}/collaborators`);
            return data;
        },
        enabled: !!projectId,
    });
};

export const useAddCollaborator = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, usernameOrEmail }: { projectId: number; usernameOrEmail: string }) => {
            const { data } = await api.post<User>(`/projects/${projectId}/collaborators`, { username_or_email: usernameOrEmail });
            return data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['project_collaborators', variables.projectId] });
            queryClient.invalidateQueries({ queryKey: ['projects'] }); // In case list changes? Maybe not needed but safe.
        },
    });
};

export const useRemoveCollaborator = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, userId }: { projectId: number; userId: number }) => {
            await api.delete(`/projects/${projectId}/collaborators/${userId}`);
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['project_collaborators', variables.projectId] });
        },
    });
};

export const useDeleteProject = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (projectId: number) => {
            const { data } = await api.delete(`/projects/${projectId}`);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
        },
    });
};

export const useIngestProject = () => {
    return useMutation({
        mutationFn: async (projectId: number) => {
            const { data } = await api.post(`/projects/${projectId}/ingest`);
            return data;
        },
    });
};

export const useIngestInstall = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (installId: number) => {
            const { data } = await api.post(`/installs/${installId}/ingest`);
            return data;
        },
        onSuccess: (_, installId) => {
            queryClient.invalidateQueries({ queryKey: ['install', installId] });
            queryClient.invalidateQueries({ queryKey: ['install_timeseries', installId] });
        },
    });
};

export const useImportProjectCsv = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (file: File) => {
            const formData = new FormData();
            formData.append('file', file);
            const { data } = await api.post('/projects/import-csv', formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['projects'] });
        },
    });
};

export const useProject = (id: number) => {
    return useQuery({
        queryKey: ['projects', id],
        queryFn: async () => {
            const { data } = await api.get<Project>(`/projects/${id}`);
            return data;
        },
        enabled: !!id,
    });
};

// Sites
export const useSites = (projectId: number) => {
    return useQuery({
        queryKey: ['sites', projectId],
        queryFn: async () => {
            const { data } = await api.get<Site[]>(`/projects/${projectId}/sites`);
            return data;
        },
        enabled: !!projectId,
    });
};

// Monitors
export const useMonitors = (siteId: number) => {
    return useQuery({
        queryKey: ['monitors', siteId],
        queryFn: async () => {
            const { data } = await api.get<Monitor[]>(`/sites/${siteId}/monitors`);
            return data;
        },
        enabled: !!siteId,
    });
};

export const useProjectMonitors = (projectId: number) => {
    return useQuery({
        queryKey: ['monitors', projectId],
        queryFn: async () => {
            const { data } = await api.get<Monitor[]>(`/projects/${projectId}/monitors`);
            return data;
        },
        enabled: !!projectId,
        refetchOnWindowFocus: true,
    });
};

export const useMonitor = (id: number) => {
    return useQuery({
        queryKey: ['monitors', id],
        queryFn: async () => {
            const { data } = await api.get<Monitor>(`/monitors/${id}`);
            return data;
        },
        enabled: !!id,
        retry: false,
    });
};

// Installs
export const useInstalls = (monitorId: number) => {
    return useQuery({
        queryKey: ['installs', monitorId],
        queryFn: async () => {
            const { data } = await api.get<Install[]>(`/monitors/${monitorId}/installs`);
            return data;
        },
        enabled: !!monitorId,
    });
};

export const useSiteInstalls = (siteId: number) => {
    return useQuery({
        queryKey: ['installs', siteId],
        queryFn: async () => {
            const { data } = await api.get<Install[]>(`/sites/${siteId}/installs`);
            return data;
        },
        enabled: !!siteId,
    });
};

export const useProjectInstalls = (projectId: number) => {
    return useQuery({
        queryKey: ['installs', 'project', projectId],
        queryFn: async () => {
            const { data } = await api.get<Install[]>(`/projects/${projectId}/installs`);
            return data;
        },
        enabled: !!projectId,
    });
};

export const useInstall = (installId: number) => {
    return useQuery({
        queryKey: ['install', installId],
        queryFn: async () => {
            const { data } = await api.get<Install>(`/installs/${installId}`);
            return data;
        },
        enabled: !!installId,
    });
};

export const useDeleteInstall = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (installId: number) => {
            await api.delete(`/installs/${installId}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['installs'] });
        },
    });
};

export const useUninstallInstall = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ installId, removalDate }: { installId: number; removalDate: string }) => {
            await api.put(`/installs/${installId}/uninstall`, { removal_date: removalDate });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['installs'] });
        },
    });
};

// Raw Data Settings
export interface RawDataSettings {
    id: number;
    install_id: number;
    file_path?: string;
    rainfall_file_format?: string;
    depth_file_format?: string;
    velocity_file_format?: string;
    battery_file_format?: string;
    pumplogger_file_format?: string;
    rg_tb_depth?: number;
    rg_timing_corr?: string;
    pipe_shape?: string;
    pipe_width?: number;
    pipe_height?: number;
    pipe_shape_intervals?: number;
    pipe_shape_def?: string;
    dep_corr?: string;
    vel_corr?: string;
    dv_timing_corr?: string;
    silt_levels?: string;
    pl_timing_corr?: string;
    pl_added_onoffs?: string;
}

export const useRawDataSettings = (installId: number) => {
    return useQuery({
        queryKey: ['rawDataSettings', installId],
        queryFn: async () => {
            try {
                const { data } = await api.get<RawDataSettings>(`/installs/${installId}/raw-data-settings`);
                return data;
            } catch (error: any) {
                // Return null if settings don't exist yet (404)
                if (error.response?.status === 404) {
                    return null;
                }
                throw error;
            }
        },
        enabled: !!installId,
    });
};

export const useUpdateRawDataSettings = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ installId, settings }: { installId: number; settings: Partial<RawDataSettings> }) => {
            const { data } = await api.put<RawDataSettings>(`/installs/${installId}/raw-data-settings`, settings);
            return data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['rawDataSettings', variables.installId] });
        },
    });
};

// Visits
export const useVisits = (installId: number) => {
    return useQuery({
        queryKey: ['visits', installId],
        queryFn: async () => {
            const { data } = await api.get<Visit[]>(`/installs/${installId}/visits`);
            return data;
        },
        enabled: !!installId,
    });
};

// Analysis Datasets
export interface AnalysisDataset {
    id: number;
    project_id: number;
    name: string;
    variable: string;
    imported_at: string;
    metadata_json: string;
    status: 'processing' | 'ready' | 'error';
    error_message?: string;
}

export const useAnalysisDatasets = (projectId: number) => {
    return useQuery({
        queryKey: ['analysis_datasets', projectId],
        queryFn: async () => {
            const { data } = await api.get<AnalysisDataset[]>(`/fsa/projects/${projectId}/datasets`);
            return data;
        },
        enabled: !!projectId,
    });
};

export const useUploadAnalysisDataset = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, file, datasetType }: { projectId: number; file: File; datasetType?: string }) => {
            const formData = new FormData();
            formData.append('file', file);
            if (datasetType) {
                formData.append('dataset_type', datasetType);
            }
            const { data } = await api.post<AnalysisDataset>(`/fsa/projects/${projectId}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['analysis_datasets', variables.projectId] });
        },
    });
};

export const useDeleteAnalysisDataset = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (datasetId: number) => {
            const { data } = await api.delete(`/fsa/datasets/${datasetId}`);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['analysis_datasets'] });
        },
    });
};

export const useUpdateAnalysisDataset = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ datasetId, updates }: { datasetId: number; updates: Record<string, any> }) => {
            const { data } = await api.patch(`/fsa/datasets/${datasetId}`, updates);
            return data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['analysis_datasets'] });
            queryClient.invalidateQueries({ queryKey: ['fdv_scatter', data.id] });
        },
    });
};


// Analysis - Rainfall Events
// Analysis - Rainfall Events
export const useRainfallEvents = (datasetIds: number[]) => {
    return useQuery({
        queryKey: ['rainfall_events', datasetIds],
        queryFn: async () => {
            if (!datasetIds || datasetIds.length === 0) return [];
            const { data } = await api.post<any>(`/fsa/rainfall/events`, {
                dataset_ids: datasetIds,
                params: {} // Default params
            });
            return data.events;
        },
        enabled: !!datasetIds && datasetIds.length > 0,
    });
};

// Analysis - Scatter Data
export const useFDVScatter = (
    datasetId: number,
    plotMode: string = "velocity",
    isoMin?: number,
    isoMax?: number,
    isoCount: number = 2
) => {
    return useQuery({
        queryKey: ['fdv_scatter', datasetId, plotMode, isoMin, isoMax, isoCount],
        queryFn: async () => {
            const params = new URLSearchParams({
                plot_mode: plotMode,
                iso_count: isoCount.toString()
            });

            if (isoMin !== undefined) params.append('iso_min', isoMin.toString());
            if (isoMax !== undefined) params.append('iso_max', isoMax.toString());

            const { data } = await api.get<any>(`/fsa/fdv/${datasetId}/scatter?${params}`);
            return data;
        },
        enabled: !!datasetId,
    });
};

// Analysis - FDV Time Series
export const useFDVTimeseries = (datasetId: number) => {
    return useQuery({
        queryKey: ['fdv_timeseries', datasetId],
        queryFn: async () => {
            const { data } = await api.get<any>(`/fsa/fdv/${datasetId}/timeseries`);
            return data;
        },
        enabled: !!datasetId,
    });
};

// WQ - Water Quality Data
export const useWQData = (monitorId: number) => {
    return useQuery({
        queryKey: ['wq_data', monitorId],
        queryFn: async () => {
            const { data } = await api.get<WQData[]>(`/wq/data?monitor_id=${monitorId}`);
            return data;
        },
        enabled: !!monitorId,
    });
};

// WQ - Correlation
export const useWQCorrelation = (monitorId: number, flowMonitorId: number) => {
    return useQuery({
        queryKey: ['wq_correlation', monitorId, flowMonitorId],
        queryFn: async () => {
            const { data } = await api.get(`/wq/correlation?monitor_id=${monitorId}&flow_monitor_id=${flowMonitorId}`);
            return data;
        },
        enabled: !!monitorId && !!flowMonitorId,
    });
};

// Analysis - Project Events
export interface SurveyEvent {
    id: number;
    project_id: number;
    name: string;
    event_type: string;
    start_time: string;
    end_time: string;
}

export const useProjectEvents = (projectId: number) => {
    return useQuery({
        queryKey: ['project_events', projectId],
        queryFn: async () => {
            const { data } = await api.get<SurveyEvent[]>(`/fsa/projects/${projectId}/events`);
            return data;
        },
        enabled: !!projectId,
    });
};

// Users
export interface User {
    id: number;
    username: string;
    email?: string;
    full_name?: string;
    is_active: boolean;
    is_superuser: boolean;
    role: string;
    access_fsm?: boolean;
    access_fsa?: boolean;
    access_wq?: boolean;
    access_verification?: boolean;
    access_ssd?: boolean;
}

export interface UserCreate {
    username: string;
    email?: string;
    full_name?: string;
    password: string;
    role: string;
    is_superuser?: boolean;
    is_active?: boolean;
    access_fsm?: boolean;
    access_fsa?: boolean;
    access_wq?: boolean;
    access_verification?: boolean;
    access_ssd?: boolean;
}

export interface UserUpdate {
    email?: string;
    full_name?: string;
    password?: string;
    role?: string;
    is_active?: boolean;
    is_superuser?: boolean;
    access_fsm?: boolean;
    access_fsa?: boolean;
    access_wq?: boolean;
    access_verification?: boolean;
    access_ssd?: boolean;
}

export const useUsers = () => {
    return useQuery({
        queryKey: ['users'],
        queryFn: async () => {
            const { data } = await api.get<User[]>('/users');
            return data;
        },
    });
};

export const useCurrentUser = () => {
    return useQuery({
        queryKey: ['users', 'me'],
        queryFn: async () => {
            const { data } = await api.get<User>('/users/me');
            return data;
        },
        retry: false,
    });
};

export const useCreateUser = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (newUser: UserCreate) => {
            const { data } = await api.post<User>('/users', newUser);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });
};

export const useUpdateUser = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ id, updates }: { id: number; updates: UserUpdate }) => {
            const { data } = await api.put<User>(`/users/${id}`, updates);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });
};

export const useDeleteUser = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (userId: number) => {
            const { data } = await api.delete(`/users/${userId}`);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['users'] });
        },
    });
};

// Install Timeseries Data
export interface TimeseriesVariable {
    data: Array<{ time: string; value: number | null }>;
    stats: {
        min: number | null;
        max: number | null;
        mean: number | null;
        count: number;
    };
    unit: string;
}

export interface InstallTimeseriesData {
    install_id: number;
    install_type: string;
    data_type: string;
    variables: Record<string, TimeseriesVariable>;
}

export const useInstallTimeseries = (
    installId: number,
    dataType: string = "Raw",
    startDate?: string,
    endDate?: string,
    maxPoints: number = 5000
) => {
    return useQuery({
        queryKey: ['install_timeseries', installId, dataType, startDate, endDate, maxPoints],
        queryFn: async () => {
            const params = new URLSearchParams({ data_type: dataType, max_points: maxPoints.toString() });
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            const { data } = await api.get<InstallTimeseriesData>(`/installs/${installId}/timeseries?${params}`);
            return data;
        },
        enabled: !!installId,
        keepPreviousData: true,
    });
};

export const useProcessInstall = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (installId: number) => {
            const { data } = await api.post(`/installs/${installId}/process`);
            return data;
        },
        onSuccess: (_, installId) => {
            queryClient.invalidateQueries({ queryKey: ['install_timeseries', installId] });
        },
    });
};

export const useProcessProject = () => {
    return useMutation({
        mutationFn: async (projectId: number) => {
            const { data } = await api.post(`/projects/${projectId}/process`);
            return data;
        },
    });
};

// ==========================================
// INTERIM REVIEW TYPES & HOOKS
// ==========================================

export interface Interim {
    id: number;
    project_id: number;
    start_date: string;
    end_date: string;
    status: 'draft' | 'in_progress' | 'complete' | 'locked';
    revision_of?: number;
    created_at: string;
    locked_at?: string;
    review_count?: number;
    reviews_complete?: number;
}

export interface InterimReview {
    id: number;
    interim_id: number;
    install_id: number;
    monitor_id?: number;
    install_type: string;
    // Stage 1
    data_coverage_pct?: number;
    gaps_json?: string;
    data_import_acknowledged: boolean;
    data_import_notes?: string;
    data_import_reviewer?: string;
    data_import_reviewed_at?: string;
    // Stage 2
    classification_complete: boolean;
    classification_comment?: string;
    classification_reviewer?: string;
    classification_reviewed_at?: string;
    // Stage 3
    events_complete: boolean;
    events_comment?: string;
    events_reviewer?: string;
    events_reviewed_at?: string;
    // Stage 4
    review_complete: boolean;
    review_comment?: string;
    review_reviewer?: string;
    review_reviewed_at?: string;
    annotation_count?: number;
}

export interface ReviewAnnotation {
    id: number;
    interim_review_id: number;
    variable: string;
    start_time: string;
    end_time: string;
    issue_type: 'anomaly' | 'suspect' | 'gap' | 'calibration' | 'other';
    description?: string;
    created_by?: string;
    created_at: string;
}

// Interim hooks
export const useProjectInterims = (projectId: number) => {
    return useQuery({
        queryKey: ['interims', projectId],
        queryFn: async () => {
            const { data } = await api.get<Interim[]>(`/projects/${projectId}/interims`);
            return data;
        },
        enabled: !!projectId,
    });
};

export const useInterim = (interimId: number) => {
    return useQuery({
        queryKey: ['interim', interimId],
        queryFn: async () => {
            const { data } = await api.get<Interim>(`/interims/${interimId}`);
            return data;
        },
        enabled: !!interimId,
    });
};

export const useCreateInterim = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, startDate, endDate }: { projectId: number; startDate: string; endDate: string }) => {
            const { data } = await api.post<Interim>(`/projects/${projectId}/interims`, {
                project_id: projectId,
                start_date: startDate,
                end_date: endDate,
            });
            return data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['interims', variables.projectId] });
        },
    });
};

export const useUpdateInterim = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ interimId, ...update }: { interimId: number; start_date?: string; end_date?: string; status?: string }) => {
            const { data } = await api.put<Interim>(`/interims/${interimId}`, update);
            return data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['interim', data.id] });
            queryClient.invalidateQueries({ queryKey: ['interims', data.project_id] });
        },
    });
};

export const useDeleteInterim = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (interimId: number) => {
            const { data } = await api.delete(`/interims/${interimId}`);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['interims'] });
        },
    });
};

// Interim Review hooks
export const useInterimReviews = (interimId: number) => {
    return useQuery({
        queryKey: ['interim_reviews', interimId],
        queryFn: async () => {
            const { data } = await api.get<InterimReview[]>(`/interims/${interimId}/reviews`);
            return data;
        },
        enabled: !!interimId,
    });
};

export const useInterimReview = (reviewId: number) => {
    return useQuery({
        queryKey: ['interim_review', reviewId],
        queryFn: async () => {
            const { data } = await api.get<InterimReview>(`/reviews/${reviewId}`);
            return data;
        },
        enabled: !!reviewId,
    });
};

export const useSignoffReviewStage = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ reviewId, stage, comment, reviewer }: { reviewId: number; stage: string; comment?: string; reviewer: string }) => {
            const { data } = await api.put(`/reviews/${reviewId}/signoff/${stage}`, { comment, reviewer });
            return data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['interim_review', variables.reviewId] });
            queryClient.invalidateQueries({ queryKey: ['interim_reviews'] });
        },
    });
};

export const useCalculateCoverage = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (reviewId: number) => {
            const { data } = await api.post(`/reviews/${reviewId}/calculate-coverage`);
            return data;
        },
        onSuccess: (_, reviewId) => {
            queryClient.invalidateQueries({ queryKey: ['interim_review', reviewId] });
            queryClient.invalidateQueries({ queryKey: ['interim_reviews'] });
        },
    });
};

export const useCalculateAllCoverage = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (interimId: number) => {
            const { data } = await api.post(`/interims/${interimId}/calculate-all-coverage`);
            return data;
        },
        onSuccess: (_, interimId) => {
            queryClient.invalidateQueries({ queryKey: ['interim_reviews', interimId] });
        },
    });
};

// Annotation hooks
export const useReviewAnnotations = (reviewId: number) => {
    return useQuery({
        queryKey: ['review_annotations', reviewId],
        queryFn: async () => {
            const { data } = await api.get<ReviewAnnotation[]>(`/reviews/${reviewId}/annotations`);
            return data;
        },
        enabled: !!reviewId,
    });
};

export const useCreateAnnotation = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ reviewId, ...annotation }: { reviewId: number; variable: string; start_time: string; end_time: string; issue_type: string; description?: string }) => {
            const { data } = await api.post<ReviewAnnotation>(`/reviews/${reviewId}/annotations`, {
                interim_review_id: reviewId,
                ...annotation,
            });
            return data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['review_annotations', variables.reviewId] });
            queryClient.invalidateQueries({ queryKey: ['interim_review', variables.reviewId] });
        },
    });
};

export const useDeleteAnnotation = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (annotationId: number) => {
            const { data } = await api.delete(`/annotations/${annotationId}`);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['review_annotations'] });
        },
    });
};

// ==========================================
// CLASSIFICATION HOOKS
// ==========================================

export interface DailyClassification {
    id: number;
    date: string;
    ml_classification: string;
    ml_confidence: number;
    manual_classification?: string;
    override_reason?: string;
    override_by?: string;
    override_at?: string;
}

export const useReviewClassifications = (reviewId: number) => {
    return useQuery({
        queryKey: ['review_classifications', reviewId],
        queryFn: async () => {
            const { data } = await api.get<DailyClassification[]>(`/reviews/${reviewId}/classifications`);
            return data;
        },
        enabled: !!reviewId,
    });
};

export const useRunClassification = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (reviewId: number) => {
            const { data } = await api.post(`/reviews/${reviewId}/classify`);
            return data;
        },
        onSuccess: (_, reviewId) => {
            queryClient.invalidateQueries({ queryKey: ['review_classifications', reviewId] });
        },
    });
};

export const useOverrideClassification = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ classificationId, manual_classification, override_reason }: { classificationId: number; manual_classification: string; override_reason?: string }) => {
            const { data } = await api.put(`/classifications/${classificationId}/override`, {
                manual_classification,
                override_reason,
            });
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['review_classifications'] });
        },
    });
};

export const useModelsStatus = () => {
    return useQuery({
        queryKey: ['classification_models_status'],
        queryFn: async () => {
            const { data } = await api.get<Record<string, boolean>>(`/classification/models-status`);
            return data;
        },
    });
};

// ==========================================
// FSM Events (Project-level rainfall events)
// ==========================================

export interface FsmEvent {
    id: number;
    project_id: number;
    start_time: string;
    end_time: string;
    event_type: string;  // "Storm", "No Event", "Dry Day"
    total_rainfall_mm?: number;
    max_intensity_mm_hr?: number;
    preceding_dry_hours?: number;
    reviewed: boolean;
    review_comment?: string;
    reviewed_by?: string;
    reviewed_at?: string;
    created_at: string;
}

export const useFsmProjectEvents = (projectId: number, startDate?: string, endDate?: string) => {
    return useQuery({
        queryKey: ['fsm_project_events', projectId, startDate, endDate],
        queryFn: async () => {
            const params = new URLSearchParams();
            if (startDate) params.append('start_date', startDate);
            if (endDate) params.append('end_date', endDate);
            const { data } = await api.get<FsmEvent[]>(`/projects/${projectId}/events?${params.toString()}`);
            return data;
        },
        enabled: !!projectId,
    });
};

export interface DetectEventsParams {
    projectId: number;
    startDate: string;
    endDate: string;
    minIntensity?: number;
    minDurationHours?: number;
    precedingDryHours?: number;
}

export const useDetectEvents = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, startDate, endDate, minIntensity, minDurationHours, precedingDryHours }: DetectEventsParams) => {
            const params = new URLSearchParams({
                start_date: startDate,
                end_date: endDate,
            });
            if (minIntensity !== undefined) params.append('min_intensity', minIntensity.toString());
            if (minDurationHours !== undefined) params.append('min_duration_hours', minDurationHours.toString());
            if (precedingDryHours !== undefined) params.append('preceding_dry_hours', precedingDryHours.toString());

            const { data } = await api.post(`/projects/${projectId}/events/detect?${params.toString()}`);
            return data;
        },
        onSuccess: (_, { projectId }) => {
            queryClient.invalidateQueries({ queryKey: ['fsm_project_events', projectId] });
        },
    });
};

export const useUpdateEvent = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ eventId, ...updates }: { eventId: number; reviewed?: boolean; review_comment?: string; event_type?: string }) => {
            const { data } = await api.put<FsmEvent>(`/events/${eventId}`, updates);
            return data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['fsm_project_events', data.project_id] });
        },
    });
};

export const useDeleteEvent = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (eventId: number) => {
            const { data } = await api.delete(`/events/${eventId}`);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['fsm_project_events'] });
        },
    });
};

export interface SSDProject {
    id: number;
    name: string;
    client: string;
    job_number: string;
    description?: string;
    created_at: string;
}

export interface SSDProjectCreate {
    name: string;
    client: string;
    job_number: string;
    description?: string;
}

export interface SSDAnalysisConfig {
    cso_name: string;
    overflow_link: string;
    continuation_link: string;
    run_suffix: string;
    start_date: string;
    end_date: string;
    spill_target_entire: number;
    spill_target_bathing: number;
    bathing_season_start: string;
    bathing_season_end: string;
    pff_increase: number;
    tank_volume?: number;
    pump_rate: number;
    pumping_mode: 'Fixed' | 'Variable';
    flow_return_threshold: number;
    depth_return_threshold: number;
    time_delay: number;
    spill_flow_threshold: number;
    spill_volume_threshold: number;
}

export interface SpillEvent {
    start_time: string;
    end_time: string;
    duration_hours: number;
    volume_m3: number;
    peak_flow_m3s: number;
    is_bathing_season: boolean;
}

export interface SSDAnalysisResult {
    success: boolean;
    cso_name: string;
    converged: boolean;
    iterations: number;
    final_storage_m3: number;
    spill_count: number;
    bathing_spill_count: number;
    total_spill_volume_m3: number;
    bathing_spill_volume_m3: number;
    total_spill_duration_hours: number;
    spill_events: SpillEvent[];
    error?: string;
}

export interface UploadedFile {
    filename: string;
    size_bytes: number;
    uploaded_at: string;
}

// SSD Hooks
export function useSSDProjects() {
    return useQuery({
        queryKey: ['ssd-projects'],
        queryFn: async () => {
            const response = await api.get<SSDProject[]>('/ssd/projects');
            return response.data;
        },
    });
}

export function useSSDProject(projectId: number) {
    return useQuery({
        queryKey: ['ssd-project', projectId],
        queryFn: async () => {
            const response = await api.get<SSDProject>(`/ssd/projects/${projectId}`);
            return response.data;
        },
        enabled: !!projectId,
    });
}

export function useCreateSSDProject() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (newProject: SSDProjectCreate) => {
            const response = await api.post('/ssd/projects', newProject);
            return response.data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['ssd-projects'] });
        },
    });
}

export function useSSDFiles(projectId: number) {
    return useQuery({
        queryKey: ['ssd-files', projectId],
        queryFn: async () => {
            const response = await api.get<UploadedFile[]>(`/ssd/projects/${projectId}/files`);
            return response.data;
        },
        enabled: !!projectId,
    });
}

export function useSSDUpload() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, files }: { projectId: number; files: File[] }) => {
            const formData = new FormData();
            files.forEach((file) => {
                formData.append('flow_files', file);
            });
            const response = await api.post(`/ssd/projects/${projectId}/upload`, formData, {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            });
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-files', variables.projectId] });
        },
    });
}

export function useDeleteSSDFile() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, filename }: { projectId: number; filename: string }) => {
            const response = await api.delete(`/ssd/projects/${projectId}/files/${filename}`);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-files', variables.projectId] });
        },
    });
}

export function useSSDAnalysis() {
    return useMutation({
        mutationFn: async ({ projectId, config }: { projectId: number; config: SSDAnalysisConfig }) => {
            const response = await api.post<SSDAnalysisResult>(`/ssd/projects/${projectId}/analyze`, config);
            return response.data;
        },
    });
}

// New scenario-based analysis hook
export interface ScenarioAnalysisResult {
    success: boolean;
    message: string;
    scenarios: {
        scenario_id: number;
        scenario_name: string;
        cso_name: string;
        config_name: string;
        status: string;
        message: string;
    }[];
}

export function useSSDScenarioAnalysis() {
    return useMutation({
        mutationFn: async ({ projectId, scenarioIds }: { projectId: number; scenarioIds: number[] }) => {
            const response = await api.post<ScenarioAnalysisResult>(`/ssd/projects/${projectId}/analyze-scenarios`, {
                scenario_ids: scenarioIds
            });
            return response.data;
        },
    });
}

// ==========================================
// CSO ASSETS
// ==========================================

export interface CSOAsset {
    id: number;
    project_id: number;
    name: string;
    overflow_links: string[];
    continuation_link: string;
    is_effective_link: boolean;
    effective_link_components: string[] | null;
    created_at: string;
}

export interface CSOAssetCreate {
    name: string;
    overflow_links: string[];
    continuation_link: string;
    is_effective_link?: boolean;
    effective_link_components?: string[] | null;
}

export interface CSOAssetUpdate {
    name?: string;
    overflow_links?: string[];
    continuation_link?: string;
    is_effective_link?: boolean;
    effective_link_components?: string[] | null;
}

// Get available link names from uploaded CSVs
export function useSSDLinks(projectId: number) {
    return useQuery({
        queryKey: ['ssd-links', projectId],
        queryFn: async () => {
            const response = await api.get<string[]>(`/ssd/projects/${projectId}/links`);
            return response.data;
        },
        enabled: !!projectId,
    });
}

export interface DateRange {
    min_date: string | null;
    max_date: string | null;
}

// Get date range from uploaded CSV files
export function useSSDDateRange(projectId: number) {
    return useQuery({
        queryKey: ['ssd-date-range', projectId],
        queryFn: async () => {
            const response = await api.get<DateRange>(`/ssd/projects/${projectId}/date-range`);
            return response.data;
        },
        enabled: !!projectId,
    });
}

// List CSO assets
export function useSSDCSOAssets(projectId: number) {
    return useQuery({
        queryKey: ['ssd-cso-assets', projectId],
        queryFn: async () => {
            const response = await api.get<CSOAsset[]>(`/ssd/projects/${projectId}/cso-assets`);
            return response.data;
        },
        enabled: !!projectId,
    });
}

// Create CSO asset
export function useCreateCSOAsset() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, asset }: { projectId: number; asset: CSOAssetCreate }) => {
            const response = await api.post<CSOAsset>(`/ssd/projects/${projectId}/cso-assets`, asset);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-cso-assets', variables.projectId] });
        },
    });
}

// Update CSO asset
export function useUpdateCSOAsset() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, assetId, update }: { projectId: number; assetId: number; update: CSOAssetUpdate }) => {
            const response = await api.put<CSOAsset>(`/ssd/projects/${projectId}/cso-assets/${assetId}`, update);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-cso-assets', variables.projectId] });
        },
    });
}

// Delete CSO asset
export function useDeleteCSOAsset() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, assetId }: { projectId: number; assetId: number }) => {
            const response = await api.delete(`/ssd/projects/${projectId}/cso-assets/${assetId}`);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-cso-assets', variables.projectId] });
        },
    });
}

// ==========================================
// ANALYSIS CONFIGURATIONS
// ==========================================

export interface AnalysisConfigDB {
    id: number;
    project_id: number;
    name: string;
    mode: string;
    model: number;
    start_date: string;
    end_date: string;
    spill_target: number;
    spill_target_bathing: number | null;
    bathing_season_start: string | null;
    bathing_season_end: string | null;
    spill_flow_threshold: number;
    spill_volume_threshold: number;
    created_at: string;
}

export interface AnalysisConfigDBCreate {
    name: string;
    mode: string;
    model: number;
    start_date: string;
    end_date: string;
    spill_target: number;
    spill_target_bathing?: number | null;
    bathing_season_start?: string | null;
    bathing_season_end?: string | null;
    spill_flow_threshold?: number;
    spill_volume_threshold?: number;
}

export interface AnalysisConfigDBUpdate {
    name?: string;
    mode?: string;
    model?: number;
    start_date?: string;
    end_date?: string;
    spill_target?: number;
    spill_target_bathing?: number | null;
    bathing_season_start?: string | null;
    bathing_season_end?: string | null;
    spill_flow_threshold?: number;
    spill_volume_threshold?: number;
}

// List analysis configs
export function useSSDAnalysisConfigs(projectId: number) {
    return useQuery({
        queryKey: ['ssd-analysis-configs', projectId],
        queryFn: async () => {
            const response = await api.get<AnalysisConfigDB[]>(`/ssd/projects/${projectId}/analysis-configs`);
            return response.data;
        },
        enabled: !!projectId,
    });
}

// Create analysis config
export function useCreateAnalysisConfig() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, config }: { projectId: number; config: AnalysisConfigDBCreate }) => {
            const response = await api.post<AnalysisConfigDB>(`/ssd/projects/${projectId}/analysis-configs`, config);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-analysis-configs', variables.projectId] });
        },
    });
}

// Update analysis config
export function useUpdateAnalysisConfig() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, configId, update }: { projectId: number; configId: number; update: AnalysisConfigDBUpdate }) => {
            const response = await api.put<AnalysisConfigDB>(`/ssd/projects/${projectId}/analysis-configs/${configId}`, update);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-analysis-configs', variables.projectId] });
        },
    });
}

// Delete analysis config
export function useDeleteAnalysisConfig() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, configId }: { projectId: number; configId: number }) => {
            const response = await api.delete(`/ssd/projects/${projectId}/analysis-configs/${configId}`);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-analysis-configs', variables.projectId] });
        },
    });
}

// ==========================================
// ANALYSIS SCENARIOS
// ==========================================

export interface AnalysisScenarioData {
    id: number;
    project_id: number;
    scenario_name: string;
    cso_asset_id: number;
    config_id: number;
    pff_increase: number;
    pumping_mode: string;
    pump_rate: number;
    time_delay: number;
    flow_return_threshold: number;
    depth_return_threshold: number;
    tank_volume: number | null;
    created_at: string;
}

export interface AnalysisScenarioCreate {
    scenario_name: string;
    cso_asset_id: number;
    config_id: number;
    pff_increase?: number;
    pumping_mode?: string;
    pump_rate?: number;
    time_delay?: number;
    flow_return_threshold?: number;
    depth_return_threshold?: number;
    tank_volume?: number | null;
}

export interface AnalysisScenarioUpdate {
    scenario_name?: string;
    cso_asset_id?: number;
    config_id?: number;
    pff_increase?: number;
    pumping_mode?: string;
    pump_rate?: number;
    time_delay?: number;
    flow_return_threshold?: number;
    depth_return_threshold?: number;
    tank_volume?: number | null;
}

// List analysis scenarios
export function useSSDScenarios(projectId: number) {
    return useQuery({
        queryKey: ['ssd-scenarios', projectId],
        queryFn: async () => {
            const response = await api.get<AnalysisScenarioData[]>(`/ssd/projects/${projectId}/scenarios`);
            return response.data;
        },
        enabled: !!projectId,
    });
}

// Create analysis scenario
export function useCreateScenario() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, scenario }: { projectId: number; scenario: AnalysisScenarioCreate }) => {
            const response = await api.post<AnalysisScenarioData>(`/ssd/projects/${projectId}/scenarios`, scenario);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-scenarios', variables.projectId] });
        },
    });
}

// Update analysis scenario
export function useUpdateScenario() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, scenarioId, update }: { projectId: number; scenarioId: number; update: AnalysisScenarioUpdate }) => {
            const response = await api.put<AnalysisScenarioData>(`/ssd/projects/${projectId}/scenarios/${scenarioId}`, update);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-scenarios', variables.projectId] });
        },
    });
}

// Delete analysis scenario
export function useDeleteScenario() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async ({ projectId, scenarioId }: { projectId: number; scenarioId: number }) => {
            const response = await api.delete(`/ssd/projects/${projectId}/scenarios/${scenarioId}`);
            return response.data;
        },
        onSuccess: (_, variables) => {
            queryClient.invalidateQueries({ queryKey: ['ssd-scenarios', variables.projectId] });
        },
    });
}


