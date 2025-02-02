import logging
from ..templatetags.custom_tags import has_any_group
from ..models.permission_model import PermissionRoleGroup
logger = logging.getLogger(__name__)

def get_dynamic_permissions(user):
    """
    Fungsi untuk mendapatkan permission dinamis berdasarkan group yang dimiliki oleh user.
    """
    permissions = {}
    try:
        # Ambil semua data dari PermissionRoleGroup
        role_groups = PermissionRoleGroup.objects.select_related('permission_group', 'group')

        for role_group in role_groups:
            try:
                # Ambil nama grup dan permission terkait
                group_name = role_group.group.name
                permission_name = role_group.permission_group.name
                
                # Jika permission belum ada, inisialisasi dengan list kosong
                if permission_name not in permissions:
                    permissions[permission_name] = []

                # Tambahkan nama grup ke dalam permission
                permissions[permission_name].append(group_name)
            except AttributeError as e:
                # Log jika terjadi kesalahan dalam pemrosesan
                logger.error(f"Error processing role group: {e}")
                continue

        # Format ulang hasil menjadi string untuk `has_any_group`
        for permission_name, groups in permissions.items():
            permissions[permission_name] = has_any_group(user, ",".join(groups))
    
    except Exception as e:
        # Log jika terjadi kesalahan saat mengambil data
        logger.error(f"Error retrieving dynamic permissions: {e}")
        return {}

    return permissions