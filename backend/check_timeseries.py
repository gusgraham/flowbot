from domain.analysis import AnalysisTimeSeries, AnalysisDataset
from database import get_session
from sqlmodel import select

session = next(get_session())

datasets = session.exec(select(AnalysisDataset)).all()
print(f'Total datasets: {len(datasets)}')

for ds in datasets:
    ts_count = len(session.exec(select(AnalysisTimeSeries).where(
        AnalysisTimeSeries.dataset_id == ds.id
    )).all())
    print(f'Dataset {ds.id} ({ds.name}): {ts_count} timeseries records')
