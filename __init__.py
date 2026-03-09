bl_info = {
    "name": "Batch Render View Layers",
    "author": "KIN",
    "version": (1, 2, 2),
    "blender": (4, 3, 0),
    "location": "View3D > Sidebar > VLRender Tab",
    "description": "Set up multiple View Layers, Cameras, Frame Ranges. Support completed flag, auto skip, move up/down tasks.",
    "category": "Render",
}

import bpy
import os
import subprocess
from bpy.props import StringProperty, IntProperty, BoolProperty, CollectionProperty, PointerProperty

# --- 1. Data Structure ---

class BatchRenderSettings(bpy.types.PropertyGroup):
    """整合原本散落在 WindowManager 的運行狀態屬性"""
    is_batch_rendering: BoolProperty(default=False)
    cancel_batch_render: BoolProperty(default=False)
    batch_progress: IntProperty(default=0)
    current_job_idx: IntProperty(default=0)
    original_render_path: StringProperty(default="")

def update_job_name(self, context):
    self.name = self.view_layer
    self.output_name = self.view_layer
    self.output_dir = self.view_layer

class RenderJobItem(bpy.types.PropertyGroup):
    name: StringProperty(name="Job Name", default="New Job")
    is_expanded: BoolProperty(name="Expanded", default=True)
    frame_start: IntProperty(name="Start Frame", default=1)
    frame_end: IntProperty(name="End Frame", default=2)
    view_layer: StringProperty(name="View Layer", default="ViewLayer", update=update_job_name)
    camera: PointerProperty(name="Camera", type=bpy.types.Object, poll=lambda self, obj: obj.type == 'CAMERA')
    output_dir: StringProperty(
        name="Subfolder",
        description="Create a folder under the default render path; blank = direct output"
    )
    output_name: StringProperty(name="File Name", default="render_out")
    is_completed: BoolProperty(
        name="Completed",
        default=False,
        description="Mark as done → will be skipped in next batch render"
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
    
    if data.cancel_batch_render or data.current_job_idx >= len(scene.render_jobs):
        finish_batch()
        return

    jobs = scene.render_jobs
    
    # 自動跳過已完成的任務
    while data.current_job_idx < len(jobs) and jobs[data.current_job_idx].is_completed:
        data.current_job_idx += 1
    
    if data.current_job_idx >= len(jobs):
        finish_batch()
        return

    job = jobs[data.current_job_idx]
    
    if job.camera: scene.camera = job.camera
    for vl in scene.view_layers: vl.use = (vl.name == job.view_layer)
    scene.frame_start, scene.frame_end = job.frame_start, job.frame_end
    
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
        
    print("Batch Render Engine: Finished")

# --- 4. Handlers ---

@bpy.app.handlers.persistent
def render_pre_handler(scene):
    if bpy.context.window_manager.batch_render_data.cancel_batch_render:
        raise RuntimeError("User Requested Stop")

@bpy.app.handlers.persistent
def render_complete_handler(scene):
    wm = bpy.context.window_manager
    data = wm.batch_render_data
    jobs = bpy.context.scene.render_jobs
    
    if data.current_job_idx < len(jobs):
        jobs[data.current_job_idx].is_completed = True
    
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
            box.label(text=f"Task: {data.current_job_idx + 1} / {len(scene.render_jobs)}", icon='INFO')
            layout.operator("batchrender.stop_execution", icon='CANCEL', text="Stop Rendering Now")
            return

        layout.separator()
        layout.operator("batchrender.add_job", icon='ADD', text="Add New Task")
        
        for index, job in enumerate(scene.render_jobs):
            box = layout.box()
            col = box.column(align=True)
            
            row = col.row(align=True)
            icon = 'DOWNARROW_HLT' if job.is_expanded else 'RIGHTARROW'
            row.prop(job, "is_expanded", icon=icon, emboss=False, text="")
            row.prop(job, "name", text="")
            
            completed_icon = 'CHECKMARK' if job.is_completed else 'BLANK1'
            row.label(text="", icon=completed_icon)
            
            sub = row.row(align=True)
            sub.alignment = 'RIGHT'
            
            if index > 0:
                op = sub.operator("batchrender.move_up", text="", icon='TRIA_UP')
                op.index = index
            else:
                sub.label(text="", icon='BLANK1')
            
            if index < len(scene.render_jobs) - 1:
                op = sub.operator("batchrender.move_down", text="", icon='TRIA_DOWN')
                op.index = index
            else:
                sub.label(text="", icon='BLANK1')
            
            sub.operator("batchrender.remove_job", text="", icon='X').index = index
            
            if job.is_expanded:
                col.separator(factor=0.5)
                col.prop_search(job, "view_layer", scene, "view_layers", text="View Layer")
                col.prop(job, "camera", text="Camera")
                
                row = col.row(align=True)
                row.prop(job, "frame_start", text="Start")
                row.prop(job, "frame_end", text="End")
                
                col.prop(job, "output_name", text="File Name")
                col.prop(job, "output_dir", text="Folder")
                
                col.separator(factor=0.8)
                col.prop(job, "is_completed", text="Completed (skip next time)")

        if len(scene.render_jobs) > 0:
            layout.separator()
            layout.operator("batchrender.start_engine", icon='RENDER_ANIMATION', text="Start Batch Render")

        layout.operator("batchrender.reset_completed", icon='FILE_REFRESH', text="Reset All Completed Flags")
        layout.operator("batchrender.open_folder", icon='FILE_FOLDER', text="Open Output Folder")

# --- 6. Operators ---

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
        self.report({'INFO'}, "Stopping... finishing current frame.")
        return {'FINISHED'}

class BATCHRENDER_OT_add_job(bpy.types.Operator):
    bl_idname = "batchrender.add_job"
    bl_label = "Add"
    def execute(self, context):
        job = context.scene.render_jobs.add()
        cameras = [obj for obj in context.scene.objects if obj.type == 'CAMERA']
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

class BATCHRENDER_OT_reset_completed(bpy.types.Operator):
    bl_idname = "batchrender.reset_completed"
    bl_label = "Reset All Completed"
    def execute(self, context):
        for job in context.scene.render_jobs:
            job.is_completed = False
        self.report({'INFO'}, "All completed flags have been reset")
        return {'FINISHED'}

class BATCHRENDER_OT_move_up(bpy.types.Operator):
    bl_idname = "batchrender.move_up"
    bl_label = "Move Task Up"
    index: IntProperty()
    def execute(self, context):
        jobs = context.scene.render_jobs
        if self.index <= 0: return {'CANCELLED'}
        jobs.move(self.index, self.index - 1)
        return {'FINISHED'}

class BATCHRENDER_OT_move_down(bpy.types.Operator):
    bl_idname = "batchrender.move_down"
    bl_label = "Move Task Down"
    index: IntProperty()
    def execute(self, context):
        jobs = context.scene.render_jobs
        if self.index >= len(jobs) - 1: return {'CANCELLED'}
        jobs.move(self.index, self.index + 1)
        return {'FINISHED'}

# --- 7. Registration ---

classes = (
    BatchRenderSettings,
    RenderJobItem,
    BATCHRENDER_PT_pro_panel,
    BATCHRENDER_OT_open_folder,
    BATCHRENDER_OT_start_engine,
    BATCHRENDER_OT_stop_execution,
    BATCHRENDER_OT_add_job,
    BATCHRENDER_OT_remove_job,
    BATCHRENDER_OT_reset_completed,
    BATCHRENDER_OT_move_up,
    BATCHRENDER_OT_move_down,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.render_jobs = CollectionProperty(type=RenderJobItem)
    bpy.types.WindowManager.batch_render_data = PointerProperty(type=BatchRenderSettings)

def unregister():
    # 移除屬性
    del bpy.types.Scene.render_jobs
    del bpy.types.WindowManager.batch_render_data
    
    # 註銷類別
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 清除 Handlers
    if render_complete_handler in bpy.app.handlers.render_complete:
        bpy.app.handlers.render_complete.remove(render_complete_handler)
    if render_pre_handler in bpy.app.handlers.render_pre:
        bpy.app.handlers.render_pre.remove(render_pre_handler)

if __name__ == "__main__":
    register()