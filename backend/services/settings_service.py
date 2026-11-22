from backend.models import SystemSettings


def get_settings() -> SystemSettings:
    doc = SystemSettings.objects(setting_key="global").first()
    if not doc:
        doc = SystemSettings(setting_key="global", site_name="PHIMHAY-GUI")
        doc.save()
    return doc


def public_settings_dict(doc: SystemSettings) -> dict:
    return {
        "siteName": doc.site_name,
        "logo": doc.logo or "",
        "bannerImages": doc.banner_images or [],
        "maintenanceMode": doc.maintenance_mode,
        "registrationEnabled": doc.registration_enabled,
        "commentsEnabled": doc.comments_enabled,
    }


def admin_settings_dict(doc: SystemSettings) -> dict:
    return {
        **public_settings_dict(doc),
        "updatedAt": doc.updated_at.isoformat() if doc.updated_at else None,
    }
