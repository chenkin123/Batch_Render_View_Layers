bl_info = {
    "name": "Batch Render View Layers",
    "author": "KIN",
    "version": (1, 2, 3),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > VLRender Tab",
    "description": "Batch render selected tasks and auto-uncheck upon completion.",
    "category": "Render",
}

import bpy
import os
import subprocess
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty, PointerProperty

# --- 1. Data Structure ---

class BatchRenderSettings(bpy.types.PropertyGroup):
    is_batch_rendering: BoolProperty(default=False)
    cancel_batch_render: BoolProperty(default=False)
    batch_progress: IntProperty(default=0)
    current_job_idx: IntProperty(default=0)
    original_render_path: StringProperty(default="")

def update_job_name(self, context):
    self.name = self.view_layer
    self.output_name = self.view_layer
    self.output_dir = self.view_layer

def update_view_layer(self, context):
    self.name = self.view_layer
    self.output_name = self.view_layer
    self.output_dir = self.view_layer
    # 即時切換 View Layer
    scene = context.scene
    if self.view_layer and self.view_layer in scene.view_layers:
        vl_names = [vl.name for vl in scene.view_layers]
        idx = vl_names.index(self.view_layer)
        context.window.view_layer = scene.view_layers[idx]

def update_camera(self, context):
    # 即時切換 Active Camera
    if self.camera:
        context.scene.camera = self.camera

class RenderJobItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Job Name", default="New Job")
    is_expanded: BoolProperty(name="Expanded", default=True)
    frame_start: IntProperty(name="Start Frame", default=1)
    frame_end: IntProperty(name="End Frame", default=2)
    view_layer: StringProperty(name="View Layer", default="ViewLayer", update=update_view_layer)
    camera: PointerProperty(name="Camera", type=bpy.types.Object, poll=lambda self, obj: obj.type == 'CAMERA', update=update_camera)
    output_dir: StringProperty(name="Subfolder")
    output_name: StringProperty(name="File Name", default="render_out")
    
    do_render: BoolProperty(
        name="Enable Render",
        default=True,
        description="Check to include in batch; will auto-uncheck when done"
    )

# --- 2. Helper Functions ---

def get_absolute_render_path():
    scene = bpy.context.scene
    raw_path = scene.render.filepath
    if not raw_path: return None
    return os.path.dirname(bpy.path.abspath(raw_path))

def open_directory(path):
    if path and os.path.exists(path):
        try:
            if os.name == 'nt': os.startfile(path)
            else:
                cmd = 'open' if os.uname().sysname == 'Darwin' else 'xdg-open'
                subprocess.Popen([cmd, path])
            return True
        except: return False
    return False

# --- 3. Core Logic Engine ---

def run_next_job():
    scene = bpy.context.scene
    wm = bpy.context.window_manager
    data = wm.batch_render_data
    jobs = scene.render_jobs
    
    if data.cancel_batch_render or data.current_job_idx >= len(jobs):
        finish_batch()
        return

    # 尋找下一個「有勾選」的任務
    found_job = False
    while data.current_job_idx < len(jobs):
        if jobs[data.current_job_idx].do_render:
            found_job = True
            break
        data.current_job_idx += 1
    
    if not found_job:
        finish_batch()
        return

    job = jobs[data.current_job_idx]
    
    # 設置算圖環境
    if job.camera: scene.camera = job.camera
    for vl in scene.view_layers: vl.use = (vl.name == job.view_layer)
    scene.frame_start, scene.frame_end = job.frame_start, job.frame_end
    
    # 路徑處理
    raw_path = data.original_render_path
    base_dir = os.path.dirname(bpy.path.abspath(raw_path)) if raw_path else None
    
    if base_dir:
        if job.output_dir:
            base_dir = os.path.join(base_dir, job.output_dir)
            if not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)
        scene.render.filepath = os.path.join(base_dir, job.output_name)
    
    data.batch_progress = int((data.current_job_idx / len(jobs)) * 100)
    bpy.ops.render.render('INVOKE_DEFAULT', animation=True)

def finish_batch():
    wm = bpy.context.window_manager
    data = wm.batch_render_data
    data.is_batch_rendering = False
    
    if render_complete_handler in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(render_complete_handler)
    if render_pre_handler in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.remove(render_pre_handler)
    
    scene = bpy.context.scene
    if data.original_render_path:
        scene.render.filepath = data.original_render_path
    print("Batch Render: Process Finished")

# --- 4. Handlers ---

@bpy.app.handlers.persistent
def render_pre_handler(scene):
    if bpy.context.window_manager.batch_render_data.cancel_batch_render:
        raise RuntimeError("User Stopped")

@bpy.app.handlers.persistent
def render_complete_handler(scene):
    wm = bpy.context.window_manager
    data = wm.batch_render_data
    jobs = bpy.context.scene.render_jobs
    
    # 算完後自動「取消勾選」
    if data.current_job_idx < len(jobs):
        jobs[data.current_job_idx].do_render = False
    
    data.current_job_idx += 1
    bpy.app.timers.register(run_next_job, first_interval=1.0)

# --- 5. UI Panel ---

class BATCHRENDER_PT_pro_panel(bpy.types.Panel):
    bl_label = "Batch Render View Layers"
    bl_idname = "BATCHRENDER_PT_pro_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'VLRender'

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        wm = context.window_manager
        data = wm.batch_render_data

        if data.is_batch_rendering:
            box = layout.box()
            box.label(text=f"Progress: {data.batch_progress}%", icon='RENDER_ANIMATION')
            layout.operator("batchrender.stop_execution", icon='CANCEL', text="Stop Rendering Now")
            return

        layout.operator("batchrender.add_job", icon='ADD', text="Add New Task")
        
        for index, job in enumerate(scene.render_jobs):
            box = layout.box()
            col = box.column(align=True)
            
            # 標題列：待渲染=正常色，完成/跳過=灰色
            header_row = col.row(align=True)
            header_row.active = job.do_render

            row = header_row.row(align=True)
            # 展開開關
            expand_icon = 'DOWNARROW_HLT' if job.is_expanded else 'RIGHTARROW'
            row.prop(job, "is_expanded", icon=expand_icon, emboss=False, text="")
            
            # 勾選框（控制是否算圖）
            row.prop(job, "do_render", text="")
            
            # 名稱顯示（收起時點名稱可預覽）
            if not job.is_expanded:
                op = row.operator("batchrender.preview_job", text=job.name, emboss=False)
                op.index = index
            else:
                row.prop(job, "name", text="")
            
            # 刪除按鈕
            row.operator("batchrender.remove_job", text="", icon='X', emboss=False).index = index
            
            if job.is_expanded:
                inner = col.column(align=True)
                inner.prop_search(job, "view_layer", scene, "view_layers", text="View Layer")
                inner.prop(job, "camera", text="Camera")
                
                split = inner.row(align=True)
                split.prop(job, "frame_start", text="Start")
                split.prop(job, "frame_end", text="End")
                
                inner.prop(job, "output_name", text="File Name")
                inner.prop(job, "output_dir", text="Folder")

        if len(scene.render_jobs) > 0:
            layout.separator()
            layout.operator("batchrender.start_engine", icon='RENDER_ANIMATION', text="Start Batch Render")

        row = layout.row(align=True)
        row.operator("batchrender.toggle_all", text="Select All").action = 'SELECT'
        row.operator("batchrender.toggle_all", text="Deselect All").action = 'DESELECT'
        layout.operator("batchrender.open_folder", icon='FILE_FOLDER', text="Open Output Folder")

# --- 6. Operators ---

class BATCHRENDER_OT_toggle_all(bpy.types.Operator):
    bl_idname = "batchrender.toggle_all"
    bl_label = "Toggle All Jobs"
    action: StringProperty()
    def execute(self, context):
        val = True if self.action == 'SELECT' else False
        for job in context.scene.render_jobs:
            job.do_render = val
        return {'FINISHED'}

class BATCHRENDER_OT_open_folder(bpy.types.Operator):
    bl_idname = "batchrender.open_folder"
    bl_label = "Open Folder"
    def execute(self, context):
        path = get_absolute_render_path()
        if not open_directory(path):
            self.report({'WARNING'}, "Invalid path or output folder not set")
        return {'FINISHED'}

class BATCHRENDER_OT_start_engine(bpy.types.Operator):
    bl_idname = "batchrender.start_engine"
    bl_label = "Start Batch"
    def execute(self, context):
        if not get_absolute_render_path():
            self.report({'ERROR'}, "Please set an Output folder in Render Properties")
            return {'CANCELLED'}
        
        if not any(job.do_render for job in context.scene.render_jobs):
            self.report({'WARNING'}, "No tasks selected for rendering")
            return {'CANCELLED'}
            
        wm = context.window_manager
        data = wm.batch_render_data
        data.original_render_path = context.scene.render.filepath
        data.is_batch_rendering = True
        data.cancel_batch_render = False
        data.current_job_idx = 0
        
        if render_complete_handler not in bpy.app.handlers.render_complete:
            bpy.app.handlers.render_complete.append(render_complete_handler)
        if render_pre_handler not in bpy.app.handlers.render_pre:
            bpy.app.handlers.render_pre.append(render_pre_handler)
        
        run_next_job()
        return {'FINISHED'}

class BATCHRENDER_OT_stop_execution(bpy.types.Operator):
    bl_idname = "batchrender.stop_execution"
    bl_label = "Stop"
    def execute(self, context):
        context.window_manager.batch_render_data.cancel_batch_render = True
        return {'FINISHED'}

class BATCHRENDER_OT_add_job(bpy.types.Operator):
    bl_idname = "batchrender.add_job"
    bl_label = "Add"
    def execute(self, context):
        scene = context.scene
        job = scene.render_jobs.add()
        # 預設第一個 View Layer
        if scene.view_layers:
            job.view_layer = scene.view_layers[0].name
        # 預設第一個 Camera（依場景物件排序）
        cameras = [obj for obj in scene.objects if obj.type == 'CAMERA']
        if cameras:
            job.camera = cameras[0]
        return {'FINISHED'}

class BATCHRENDER_OT_remove_job(bpy.types.Operator):
    bl_idname = "batchrender.remove_job"
    bl_label = "Remove"
    index: IntProperty()
    def execute(self, context):
        context.scene.render_jobs.remove(self.index)
        return {'FINISHED'}

class BATCHRENDER_OT_preview_job(bpy.types.Operator):
    bl_idname = "batchrender.preview_job"
    bl_label = "Preview Job"
    bl_description = "Switch viewport to this job's View Layer and Camera"
    index: IntProperty()

    def execute(self, context):
        scene = context.scene
        jobs = scene.render_jobs
        if self.index >= len(jobs):
            return {'CANCELLED'}

        job = jobs[self.index]

        # 切換 Active Camera
        if job.camera:
            scene.camera = job.camera

        # 切換 Active View Layer
        target_vl = job.view_layer
        if target_vl and target_vl in scene.view_layers:
            vl_names = [vl.name for vl in scene.view_layers]
            idx = vl_names.index(target_vl)
            context.window.view_layer = scene.view_layers[idx]

        self.report({'INFO'}, f"Previewing: {job.name} | Layer: {job.view_layer} | Camera: {job.camera.name if job.camera else 'None'}")
        return {'FINISHED'}

# --- 7. Registration ---

classes = (
    BatchRenderSettings,
    RenderJobItem,
    BATCHRENDER_PT_pro_panel,
    BATCHRENDER_OT_toggle_all,
    BATCHRENDER_OT_open_folder,
    BATCHRENDER_OT_start_engine,
    BATCHRENDER_OT_stop_execution,
    BATCHRENDER_OT_add_job,
    BATCHRENDER_OT_remove_job,
    BATCHRENDER_OT_preview_job,
)

# --- 8. View Layer Rename Sync ---

_msgbus_owner = object()

def _on_view_layer_renamed():
    for scene in bpy.data.scenes:
        vl_names = {vl.name for vl in scene.view_layers}
        for job in scene.render_jobs:
            if job.view_layer not in vl_names:
                used = {j.view_layer for j in scene.render_jobs}
                candidates = vl_names - used
                if len(candidates) == 1:
                    job["view_layer"] = candidates.pop()

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.render_jobs = CollectionProperty(type=RenderJobItem)
    bpy.types.WindowManager.batch_render_data = PointerProperty(type=BatchRenderSettings)
    bpy.msgbus.subscribe_rna(
        key=(bpy.types.ViewLayer, "name"),
        owner=_msgbus_owner,
        args=(),
        notify=_on_view_layer_renamed,
    )

def unregister():
    bpy.msgbus.clear_by_owner(_msgbus_owner)
    del bpy.types.Scene.render_jobs
    del bpy.types.WindowManager.batch_render_data
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if render_complete_handler in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(render_complete_handler)
    if render_pre_handler in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.remove(render_pre_handler)
    del bpy.types.Scene.render_jobs
    del bpy.types.WindowManager.batch_render_data
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    if render_complete_handler in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(render_complete_handler)
    if render_pre_handler in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.remove(render_pre_handler)

if __name__ == "__main__":
    register()
