from datetime import datetime
from sqlmodel import Session, select
from database import engine
from domain.project import Project, Site, Install
from domain.monitor import Monitor

def seed_data():
    with Session(engine) as session:
        # 1. Check if project exists
        existing_project = session.exec(select(Project).where(Project.job_number == "J1001")).first()
        if existing_project:
            print("Data already seeded!")
            return

        # 2. Create Project
        project = Project(
            job_number="J1001",
            job_name="Demo Project",
            client="Acme Corp",
            survey_start_date=datetime.now()
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        print(f"Created Project: {project.job_name}")

        # 3. Create Site
        site = Site(
            site_id="S01",
            project_id=project.id,
            address="123 Demo St",
            site_type="Flow Monitor"
        )
        session.add(site)
        session.commit()
        session.refresh(site)
        print(f"Created Site: {site.site_id}")

        # 4. Create Monitor
        monitor = Monitor(
            monitor_asset_id="M01",
            monitor_type="Flow Monitor",
            monitor_sub_type="Detec"
        )
        session.add(monitor)
        session.commit()
        session.refresh(monitor)
        print(f"Created Monitor: {monitor.monitor_asset_id}")

        # 5. Create Install
        install = Install(
            install_id="I01",
            project_id=project.id,
            site_id=site.id,
            monitor_id=monitor.id,
            install_date=datetime.now(),
            fm_pipe_height_mm=300,
            fm_pipe_width_mm=300
        )
        session.add(install)
        session.commit()
        print(f"Created Install: {install.install_id}")

if __name__ == "__main__":
    seed_data()
