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
}

export interface UserCreate {
    username: string;
    email?: string;
    full_name?: string;
    password: string;
    role: string;
    is_superuser?: boolean;
    is_active?: boolean;
}

export interface UserUpdate {
    email?: string;
    full_name?: string;
    password?: string;
    role?: string;
    is_active?: boolean;
    is_superuser?: boolean;
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
