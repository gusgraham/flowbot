import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from './client';

// Types
export interface Project {
    id: number;
    name: string;
    client: string;
    job_number: string;
}

export interface Site {
    id: number;
    project_id: number;
    name: string;
    catchment: string;
}

export interface Monitor {
    id: number;
    site_id: number;
    name: string;
    type: string;
    status: string;
}

export interface Install {
    id: number;
    monitor_id: number;
    install_date: string;
    removal_date?: string;
    height?: number;
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
            const { data } = await api.get<AnalysisProject[]>('/analysis/projects');
            return data;
        },
    });
};

export const useAnalysisProject = (id: number) => {
    return useQuery({
        queryKey: ['analysis_projects', id],
        queryFn: async () => {
            const { data } = await api.get<AnalysisProject>(`/analysis/projects/${id}`);
            return data;
        },
        enabled: !!id,
    });
};

export const useCreateAnalysisProject = () => {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: async (newProject: AnalysisProjectCreate) => {
            const { data } = await api.post<AnalysisProject>('/analysis/projects', newProject);
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
            const { data } = await api.get<Project[]>('/projects/');
            return data;
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
    created_at: string;
    metadata_json: string;
}

export const useAnalysisDatasets = (projectId: number) => {
    return useQuery({
        queryKey: ['analysis_datasets', projectId],
        queryFn: async () => {
            const { data } = await api.get<AnalysisDataset[]>(`/analysis/projects/${projectId}/datasets`);
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
            const { data } = await api.post<AnalysisDataset>(`/analysis/projects/${projectId}/upload`, formData, {
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
            const { data } = await api.delete(`/analysis/datasets/${datasetId}`);
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['analysis_datasets'] });
        },
    });
};

// Analysis - Rainfall Events
export const useRainfallEvents = (datasetId: number) => {
    return useQuery({
        queryKey: ['rainfall_events', datasetId],
        queryFn: async () => {
            const { data } = await api.post<any>(`/analysis/events/${datasetId}/detect-storms`);
            return data.events;
        },
        enabled: !!datasetId,
    });
};

// Analysis - Scatter Data
export const useScatterData = (datasetId: number) => {
    return useQuery({
        queryKey: ['scatter', datasetId],
        queryFn: async () => {
            const { data } = await api.get<any>(`/analysis/scatter/${datasetId}`);
            return data.points;
        },
        enabled: !!datasetId,
    });
};

// Analysis - FDV Time Series
export const useFDVTimeseries = (datasetId: number) => {
    return useQuery({
        queryKey: ['fdv_timeseries', datasetId],
        queryFn: async () => {
            const { data } = await api.get<any>(`/analysis/fdv/${datasetId}/timeseries`);
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
