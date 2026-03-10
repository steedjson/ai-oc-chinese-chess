import { useAuthStore } from '../stores/auth';
import type { UserRole } from '../types';

export const useHasPermission = () => {
  const { user } = useAuthStore();
  
  const checkPermission = (allowedRoles: UserRole | UserRole[]) => {
    if (!user) return false;
    
    if (Array.isArray(allowedRoles)) {
      return allowedRoles.includes(user.role);
    }
    
    return user.role === allowedRoles;
  };

  const isSuperAdmin = user?.role === 'super_admin';
  const isOps = user?.role === 'ops';

  return {
    checkPermission,
    isSuperAdmin,
    isOps,
    role: user?.role
  };
};
