from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")
    is_active: bool = Field(True, description="是否激活")


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="角色名称")
    description: Optional[str] = Field(None, max_length=200, description="角色描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class RoleInDB(RoleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class Role(RoleInDB):
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")


class MenuBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="菜单名称")
    path: str = Field(..., min_length=1, max_length=100, description="路由路径")
    icon: Optional[str] = Field(None, max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    level: int = Field(1, ge=1, le=3, description="菜单级别")
    component: Optional[str] = Field(None, max_length=200, description="前端组件")
    sort: int = Field(0, ge=0, description="排序")
    is_active: bool = Field(True, description="是否激活")


class MenuCreate(MenuBase):
    pass


class MenuUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="菜单名称")
    path: Optional[str] = Field(None, min_length=1, max_length=100, description="路由路径")
    icon: Optional[str] = Field(None, max_length=50, description="菜单图标")
    parent_id: Optional[int] = Field(None, description="父菜单ID")
    level: Optional[int] = Field(None, ge=1, le=3, description="菜单级别")
    component: Optional[str] = Field(None, max_length=200, description="前端组件")
    sort: Optional[int] = Field(None, ge=0, description="排序")
    is_active: Optional[bool] = Field(None, description="是否激活")


class MenuInDB(MenuBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class Menu(MenuInDB):
    children: List['Menu'] = Field(default_factory=list, description="子菜单")
    permission_ids: List[int] = Field(default_factory=list, description="权限ID列表")


class PermissionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="权限名称")
    code: str = Field(..., min_length=1, max_length=50, description="权限编码")
    menu_id: Optional[int] = Field(None, description="关联菜单ID")
    description: Optional[str] = Field(None, max_length=200, description="权限描述")
    is_active: bool = Field(True, description="是否激活")


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="权限名称")
    code: Optional[str] = Field(None, min_length=1, max_length=50, description="权限编码")
    menu_id: Optional[int] = Field(None, description="关联菜单ID")
    description: Optional[str] = Field(None, max_length=200, description="权限描述")
    is_active: Optional[bool] = Field(None, description="是否激活")


class PermissionInDB(PermissionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class Permission(PermissionInDB):
    menu_name: Optional[str] = Field(None, description="关联菜单名称")


class UserRoleAssign(BaseModel):
    role_ids: List[int] = Field(..., description="角色ID列表")


class RolePermissionAssign(BaseModel):
    permission_ids: List[int] = Field(..., description="权限ID列表")


class UserWithRoles(BaseModel):
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: str
    is_active: bool
    roles: List[RoleInDB] = Field(default_factory=list)
    
    class Config:
        from_attributes = True


class MenuTree(BaseModel):
    menus: List[Menu] = Field(default_factory=list, description="菜单树")


class PermissionList(BaseModel):
    permissions: List[Permission] = Field(default_factory=list, description="权限列表")


# 为 Menu 类型添加引用
Menu.model_rebuild()


class KnowledgeBaseRoleBase(BaseModel):
    knowledge_base_id: int = Field(..., description="知识库ID")
    role_id: int = Field(..., description="角色ID")


class KnowledgeBaseRoleCreate(KnowledgeBaseRoleBase):
    pass


class KnowledgeBaseRoleInDB(KnowledgeBaseRoleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class KnowledgeBaseRole(KnowledgeBaseRoleInDB):
    knowledge_base_name: Optional[str] = Field(None, description="知识库名称")
    role_name: Optional[str] = Field(None, description="角色名称")


class KnowledgeBaseRoleList(BaseModel):
    knowledge_base_roles: List[KnowledgeBaseRole] = Field(default_factory=list, description="知识库角色列表")
