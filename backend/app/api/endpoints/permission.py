from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from ..deps import get_db, get_current_user
from ...models import Role, Menu, Permission, User, UserRole, RolePermission, KnowledgeBase
from ...models.knowledge import KnowledgeBaseRole as KBRole
from ...schemas.permission import (
    Role as RoleSchema,
    RoleCreate, RoleUpdate, RoleInDB,
    Menu as MenuSchema, MenuCreate, MenuUpdate, MenuTree,
    Permission as PermissionSchema, PermissionCreate, PermissionUpdate, PermissionList,
    UserRoleAssign, RolePermissionAssign, UserWithRoles,
    KnowledgeBaseRole as KBRoleSchema, KnowledgeBaseRoleCreate, KnowledgeBaseRoleList
)

router = APIRouter()


# 角色管理

@router.post("/roles", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建角色"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    # 检查角色名称是否已存在
    existing_role = db.query(Role).filter(Role.name == role.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名称已存在"
        )
    
    # 创建角色
    db_role = Role(**role.model_dump())
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    
    # 返回角色信息
    return RoleSchema(
        id=db_role.id,
        name=db_role.name,
        description=db_role.description,
        is_active=db_role.is_active,
        created_at=db_role.created_at,
        updated_at=db_role.updated_at,
        permission_ids=[]
    )


@router.get("/roles", response_model=List[RoleSchema])
def get_roles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色列表"""
    # 所有已登录用户都可以查看角色列表
    roles = db.query(Role).offset(skip).limit(limit).all()
    
    # 构建角色列表响应
    role_list = []
    for role in roles:
        permission_ids = [p.id for p in role.permissions]
        role_list.append(RoleSchema(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permission_ids=permission_ids
        ))
    
    return role_list


@router.get("/roles/{role_id}", response_model=RoleSchema)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取角色详情"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    permission_ids = [p.id for p in role.permissions]
    return RoleSchema(
        id=role.id,
        name=role.name,
        description=role.description,
        is_active=role.is_active,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permission_ids=permission_ids
    )


@router.put("/roles/{role_id}", response_model=RoleSchema)
def update_role(
    role_id: int,
    role_update: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新角色"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查角色名称是否已存在（如果要修改名称）
    if role_update.name and role_update.name != role.name:
        existing_role = db.query(Role).filter(Role.name == role_update.name).first()
        if existing_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名称已存在"
            )
    
    # 更新角色
    update_data = role_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
    
    db.commit()
    db.refresh(role)
    
    permission_ids = [p.id for p in role.permissions]
    return RoleSchema(
        id=role.id,
        name=role.name,
        description=role.description,
        is_active=role.is_active,
        created_at=role.created_at,
        updated_at=role.updated_at,
        permission_ids=permission_ids
    )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除角色"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查是否有用户使用该角色
    user_roles = db.query(UserRole).filter(UserRole.role_id == role_id).count()
    if user_roles > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该角色已被使用，无法删除"
        )
    
    # 删除角色权限关联
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    
    # 删除角色
    db.delete(role)
    db.commit()
    
    return None


# 菜单管理

@router.post("/menus", response_model=MenuSchema, status_code=status.HTTP_201_CREATED)
def create_menu(
    menu: MenuCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建菜单"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    # 检查路径是否已存在
    existing_menu = db.query(Menu).filter(Menu.path == menu.path).first()
    if existing_menu:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="菜单路径已存在"
        )
    
    # 创建菜单
    db_menu = Menu(**menu.model_dump())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    
    # 返回菜单信息
    return MenuSchema(
        id=db_menu.id,
        name=db_menu.name,
        path=db_menu.path,
        icon=db_menu.icon,
        parent_id=db_menu.parent_id,
        level=db_menu.level,
        component=db_menu.component,
        sort=db_menu.sort,
        is_active=db_menu.is_active,
        created_at=db_menu.created_at,
        updated_at=db_menu.updated_at,
        children=[],
        permission_ids=[]
    )


@router.get("/menus", response_model=MenuTree)
def get_menus(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取菜单树"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    # 获取所有菜单
    menus = db.query(Menu).filter(Menu.is_active == True).order_by(Menu.sort).all()
    
    # 构建菜单树
    menu_map = {menu.id: MenuSchema(
        id=menu.id,
        name=menu.name,
        path=menu.path,
        icon=menu.icon,
        parent_id=menu.parent_id,
        level=menu.level,
        component=menu.component,
        sort=menu.sort,
        is_active=menu.is_active,
        created_at=menu.created_at,
        updated_at=menu.updated_at,
        children=[],
        permission_ids=[p.id for p in menu.permissions]
    ) for menu in menus}
    
    # 构建树结构
    root_menus = []
    for menu in menus:
        if menu.parent_id is None:
            root_menus.append(menu_map[menu.id])
        else:
            if menu.parent_id in menu_map:
                menu_map[menu.parent_id].children.append(menu_map[menu.id])
    
    return MenuTree(menus=root_menus)


@router.get("/user-menus", response_model=MenuTree)
def get_user_menus(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户可访问的菜单"""
    
    user = db.query(User).options(joinedload(User.roles).joinedload(Role.permissions)).filter(User.id == current_user.id).first()
    
    if not user:
        return MenuTree(menus=[])
    
    user_role_ids = [role.id for role in user.roles]
    
    if not user_role_ids:
        return MenuTree(menus=[])
    
    all_permission_ids = set()
    for role in user.roles:
        if role.permissions:
            for perm in role.permissions:
                all_permission_ids.add(perm.id)
    
    menus = db.query(Menu).options(joinedload(Menu.permissions)).filter(Menu.is_active == True).order_by(Menu.sort).all()
    
    accessible_menus = []
    for menu in menus:
        # 如果菜单没有关联权限，默认显示（用于不需要权限的菜单）
        # 或者菜单有权限且用户有该权限
        if not menu.permissions or len(menu.permissions) == 0:
            accessible_menus.append(menu)
        else:
            menu_perm_ids = set(p.id for p in menu.permissions)
            if menu_perm_ids.intersection(all_permission_ids):
                accessible_menus.append(menu)
    
    menu_map = {menu.id: MenuSchema(
        id=menu.id,
        name=menu.name,
        path=menu.path,
        icon=menu.icon,
        parent_id=menu.parent_id,
        level=menu.level,
        component=menu.component,
        sort=menu.sort,
        is_active=menu.is_active,
        created_at=menu.created_at,
        updated_at=menu.updated_at,
        children=[],
        permission_ids=[p.id for p in menu.permissions] if menu.permissions else []
    ) for menu in accessible_menus}
    
    root_menus = []
    for menu in accessible_menus:
        if menu.parent_id is None:
            root_menus.append(menu_map[menu.id])
        else:
            if menu.parent_id in menu_map:
                menu_map[menu.parent_id].children.append(menu_map[menu.id])
    
    return MenuTree(menus=root_menus)


@router.get("/menus/{menu_id}", response_model=MenuSchema)
def get_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取菜单详情"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    # 获取子菜单
    children = []
    for child in menu.children:
        if child.is_active:
            children.append(MenuSchema(
                id=child.id,
                name=child.name,
                path=child.path,
                icon=child.icon,
                parent_id=child.parent_id,
                level=child.level,
                component=child.component,
                sort=child.sort,
                is_active=child.is_active,
                created_at=child.created_at,
                updated_at=child.updated_at,
                children=[],
                permission_ids=[p.id for p in child.permissions]
            ))
    
    permission_ids = [p.id for p in menu.permissions]
    return MenuSchema(
        id=menu.id,
        name=menu.name,
        path=menu.path,
        icon=menu.icon,
        parent_id=menu.parent_id,
        level=menu.level,
        component=menu.component,
        sort=menu.sort,
        is_active=menu.is_active,
        created_at=menu.created_at,
        updated_at=menu.updated_at,
        children=children,
        permission_ids=permission_ids
    )


@router.put("/menus/{menu_id}", response_model=MenuSchema)
def update_menu(
    menu_id: int,
    menu_update: MenuUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新菜单"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    # 检查路径是否已存在（如果要修改路径）
    if menu_update.path and menu_update.path != menu.path:
        existing_menu = db.query(Menu).filter(Menu.path == menu_update.path).first()
        if existing_menu:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="菜单路径已存在"
            )
    
    # 更新菜单
    update_data = menu_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(menu, field, value)
    
    db.commit()
    db.refresh(menu)
    
    # 获取子菜单
    children = []
    for child in menu.children:
        if child.is_active:
            children.append(MenuSchema(
                id=child.id,
                name=child.name,
                path=child.path,
                icon=child.icon,
                parent_id=child.parent_id,
                level=child.level,
                component=child.component,
                sort=child.sort,
                is_active=child.is_active,
                created_at=child.created_at,
                updated_at=child.updated_at,
                children=[],
                permission_ids=[p.id for p in child.permissions]
            ))
    
    permission_ids = [p.id for p in menu.permissions]
    return MenuSchema(
        id=menu.id,
        name=menu.name,
        path=menu.path,
        icon=menu.icon,
        parent_id=menu.parent_id,
        level=menu.level,
        component=menu.component,
        sort=menu.sort,
        is_active=menu.is_active,
        created_at=menu.created_at,
        updated_at=menu.updated_at,
        children=children,
        permission_ids=permission_ids
    )


@router.delete("/menus/{menu_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu(
    menu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除菜单"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    menu = db.query(Menu).filter(Menu.id == menu_id).first()
    if not menu:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="菜单不存在"
        )
    
    # 检查是否有子菜单，如果有则递归删除
    def delete_menu_recursive(m):
        # 先删除所有子菜单
        if m.children:
            for child in m.children[:]:
                delete_menu_recursive(child)
        # 删除关联的权限
        if m.permissions:
            for perm in m.permissions[:]:
                db.delete(perm)
        # 删除菜单
        db.delete(m)
    
    delete_menu_recursive(menu)
    db.commit()
    
    return None


# 权限管理

@router.post("/permissions", response_model=PermissionSchema, status_code=status.HTTP_201_CREATED)
def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建权限"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    # 检查权限编码是否已存在
    existing_permission = db.query(Permission).filter(Permission.code == permission.code).first()
    if existing_permission:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="权限编码已存在"
        )
    
    # 创建权限
    db_permission = Permission(**permission.model_dump())
    db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    
    # 获取菜单名称
    menu_name = None
    if db_permission.menu_id:
        menu = db.query(Menu).filter(Menu.id == db_permission.menu_id).first()
        if menu:
            menu_name = menu.name
    
    # 返回权限信息
    return PermissionSchema(
        id=db_permission.id,
        name=db_permission.name,
        code=db_permission.code,
        menu_id=db_permission.menu_id,
        description=db_permission.description,
        is_active=db_permission.is_active,
        created_at=db_permission.created_at,
        updated_at=db_permission.updated_at,
        menu_name=menu_name
    )


@router.get("/permissions", response_model=PermissionList)
def get_permissions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限列表"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    permissions = db.query(Permission).offset(skip).limit(limit).all()
    
    # 构建权限列表响应
    permission_list = []
    for perm in permissions:
        menu_name = None
        if perm.menu_id:
            menu = db.query(Menu).filter(Menu.id == perm.menu_id).first()
            if menu:
                menu_name = menu.name
        
        permission_list.append(PermissionSchema(
            id=perm.id,
            name=perm.name,
            code=perm.code,
            menu_id=perm.menu_id,
            description=perm.description,
            is_active=perm.is_active,
            created_at=perm.created_at,
            updated_at=perm.updated_at,
            menu_name=menu_name
        ))
    
    return PermissionList(permissions=permission_list)


@router.get("/permissions/{permission_id}", response_model=PermissionSchema)
def get_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取权限详情"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    # 获取菜单名称
    menu_name = None
    if permission.menu_id:
        menu = db.query(Menu).filter(Menu.id == permission.menu_id).first()
        if menu:
            menu_name = menu.name
    
    return PermissionSchema(
        id=permission.id,
        name=permission.name,
        code=permission.code,
        menu_id=permission.menu_id,
        description=permission.description,
        is_active=permission.is_active,
        created_at=permission.created_at,
        updated_at=permission.updated_at,
        menu_name=menu_name
    )


@router.put("/permissions/{permission_id}", response_model=PermissionSchema)
def update_permission(
    permission_id: int,
    permission_update: PermissionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新权限"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    # 检查权限编码是否已存在（如果要修改编码）
    if permission_update.code and permission_update.code != permission.code:
        existing_permission = db.query(Permission).filter(Permission.code == permission_update.code).first()
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="权限编码已存在"
            )
    
    # 更新权限
    update_data = permission_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(permission, field, value)
    
    db.commit()
    db.refresh(permission)
    
    # 获取菜单名称
    menu_name = None
    if permission.menu_id:
        menu = db.query(Menu).filter(Menu.id == permission.menu_id).first()
        if menu:
            menu_name = menu.name
    
    return PermissionSchema(
        id=permission.id,
        name=permission.name,
        code=permission.code,
        menu_id=permission.menu_id,
        description=permission.description,
        is_active=permission.is_active,
        created_at=permission.created_at,
        updated_at=permission.updated_at,
        menu_name=menu_name
    )


@router.delete("/permissions/{permission_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_permission(
    permission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除权限"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    permission = db.query(Permission).filter(Permission.id == permission_id).first()
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="权限不存在"
        )
    
    # 检查是否有角色使用该权限
    role_permissions = db.query(RolePermission).filter(RolePermission.permission_id == permission_id).count()
    if role_permissions > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该权限已被使用，无法删除"
        )
    
    # 删除权限
    db.delete(permission)
    db.commit()
    
    return None


# 角色权限分配

@router.post("/roles/{role_id}/permissions")
def assign_role_permissions(
    role_id: int,
    assign: RolePermissionAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为角色分配权限"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    # 检查角色是否存在
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查权限是否存在
    for perm_id in assign.permission_ids:
        permission = db.query(Permission).filter(Permission.id == perm_id).first()
        if not permission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"权限ID {perm_id} 不存在"
            )
    
    # 删除现有权限关联
    db.query(RolePermission).filter(RolePermission.role_id == role_id).delete()
    
    # 创建新的权限关联
    for perm_id in assign.permission_ids:
        role_permission = RolePermission(
            role_id=role_id,
            permission_id=perm_id
        )
        db.add(role_permission)
    
    db.commit()
    
    return {"message": "权限分配成功"}


# 用户角色分配

@router.post("/users/{user_id}/roles")
def assign_user_roles(
    user_id: int,
    assign: UserRoleAssign,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """为用户分配角色"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    # 检查用户是否存在
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 检查角色是否存在
    for role_id in assign.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"角色ID {role_id} 不存在"
            )
    
    # 清除现有角色关联
    user.roles = []
    
    # 添加新的角色关联
    for role_id in assign.role_ids:
        role = db.query(Role).filter(Role.id == role_id).first()
        user.roles.append(role)
    
    db.commit()
    db.refresh(user)
    
    # 构建响应
    roles = []
    for role in user.roles:
        roles.append(RoleInDB(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at
        ))
    
    return UserWithRoles(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        roles=roles
    )


# 知识库权限配置

@router.get("/knowledge-base-roles", response_model=KnowledgeBaseRoleList)
def get_knowledge_base_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有知识库角色关联配置"""
    kb_roles = db.query(KBRole).all()
    
    result = []
    for kb_role in kb_roles:
        kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_role.knowledge_base_id).first()
        role = db.query(Role).filter(Role.id == kb_role.role_id).first()
        
        result.append(KBRoleSchema(
            id=kb_role.id,
            knowledge_base_id=kb_role.knowledge_base_id,
            role_id=kb_role.role_id,
            created_at=kb_role.created_at,
            knowledge_base_name=kb.name if kb else None,
            role_name=role.name if role else None
        ))
    
    return KnowledgeBaseRoleList(knowledge_base_roles=result)


@router.post("/knowledge-base-roles", response_model=KBRoleSchema, status_code=status.HTTP_201_CREATED)
def create_knowledge_base_role(
    kb_role_create: KnowledgeBaseRoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建知识库角色关联"""
    # 检查知识库是否存在
    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_role_create.knowledge_base_id).first()
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库不存在"
        )
    
    # 检查角色是否存在
    role = db.query(Role).filter(Role.id == kb_role_create.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )
    
    # 检查是否已存在
    existing = db.query(KBRole).filter(
        KBRole.knowledge_base_id == kb_role_create.knowledge_base_id,
        KBRole.role_id == kb_role_create.role_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该知识库角色关联已存在"
        )
    
    # 创建关联
    new_kb_role = KBRole(**kb_role_create.model_dump())
    db.add(new_kb_role)
    db.commit()
    db.refresh(new_kb_role)
    
    return KBRoleSchema(
        id=new_kb_role.id,
        knowledge_base_id=new_kb_role.knowledge_base_id,
        role_id=new_kb_role.role_id,
        created_at=new_kb_role.created_at,
        knowledge_base_name=kb.name,
        role_name=role.name
    )


@router.delete("/knowledge-base-roles/{kb_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base_role(
    kb_role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除知识库角色关联"""
    kb_role = db.query(KBRole).filter(KBRole.id == kb_role_id).first()
    if not kb_role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="知识库角色关联不存在"
        )
    
    db.delete(kb_role)
    db.commit()
    
    return None


@router.get("/knowledge-bases/accessible")
def get_accessible_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户可访问的知识库列表（用于智能问答页面）"""
    
    # admin 用户可以访问所有知识库
    if current_user.role == "admin":
        knowledge_bases = db.query(KnowledgeBase).all()
        return [{"id": kb.id, "name": kb.name, "kb_type": kb.kb_type} for kb in knowledge_bases]
    
    # 获取用户角色
    user_roles = db.query(UserRole).filter(UserRole.user_id == current_user.id).all()
    user_role_ids = [ur.role_id for ur in user_roles]
    
    if not user_role_ids:
        return []
    
    # 获取这些角色可访问的知识库
    kb_roles = db.query(KBRole).filter(
        KBRole.role_id.in_(user_role_ids)
    ).all()
    
    kb_ids = [kbr.knowledge_base_id for kbr in kb_roles]
    
    if not kb_ids:
        return []
    
    knowledge_bases = db.query(KnowledgeBase).filter(
        KnowledgeBase.id.in_(kb_ids)
    ).all()
    
    return [{"id": kb.id, "name": kb.name, "kb_type": kb.kb_type} for kb in knowledge_bases]


@router.get("/user/roles", response_model=UserWithRoles)
def get_current_user_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户角色"""
    
    user = db.query(User).options(
        joinedload(User.roles).joinedload(Role.permissions)
    ).filter(User.id == current_user.id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    roles = []
    for role in user.roles:
        roles.append(RoleInDB(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permission_ids=[p.id for p in role.permissions] if role.permissions else []
        ))
    
    return UserWithRoles(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        roles=roles
    )


# 获取用户权限

@router.get("/users/{user_id}/roles", response_model=UserWithRoles)
def get_user_roles(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户角色"""
    # 检查权限（暂时只允许admin）
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限操作"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 构建响应
    roles = []
    for role in user.roles:
        roles.append(RoleInDB(
            id=role.id,
            name=role.name,
            description=role.description,
            is_active=role.is_active,
            created_at=role.created_at,
            updated_at=role.updated_at
        ))
    
    return UserWithRoles(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        roles=roles
    )
