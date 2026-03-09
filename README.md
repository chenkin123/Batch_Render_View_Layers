<div _ngcontent-ng-c794277481="" inline-copy-host="" class="markdown markdown-main-panel stronger enable-updated-hr-color" id="model-response-message-contentr_65deef4b6a9cfa8e" aria-live="polite" aria-busy="false" dir="ltr" style="--animation-duration: 400ms; --fade-animation-function: linear;">

<h3 data-path-to-node="3">1. Core Automation Features</h3>
<ul data-path-to-node="4"><li><p data-path-to-node="4,0,0"><b data-path-to-node="4,0,0" data-index-in-node="0">Task Scheduling</b>: Create multiple render jobs, each with its own specific <b data-path-to-node="4,0,0" data-index-in-node="73">View Layer</b>, <b data-path-to-node="4,0,0" data-index-in-node="85">Camera</b>, and <b data-path-to-node="4,0,0" data-index-in-node="97">Frame Range</b>.</p></li><li><p data-path-to-node="4,1,0"><b data-path-to-node="4,1,0" data-index-in-node="0">Automatic Setting Swaps</b>: During rendering, the engine automatically switches to the designated camera and view layer for each task, eliminating the need for manual setup changes.</p></li><li><p data-path-to-node="4,2,0"><b data-path-to-node="4,2,0" data-index-in-node="0">Custom Output Paths</b>: Each job can have a unique <b data-path-to-node="4,2,0" data-index-in-node="48">subfolder</b> and <b data-path-to-node="4,2,0" data-index-in-node="62">file name</b>, preventing your renders from overwriting each other.</p></li></ul>

<h3 data-path-to-node="5">2. Smart Management Logic</h3>
<ul data-path-to-node="6">	
	<li><p data-path-to-node="6,0,0"><b data-path-to-node="6,0,0" data-index-in-node="0">Completion Tracking</b>: Once a task finishes, it is automatically marked with a "Completed" flag.</p></li>	
	<li><p data-path-to-node="6,1,0"><b data-path-to-node="6,1,0" data-index-in-node="0">Auto-Skip</b>: If you stop and restart a batch, the system <b data-path-to-node="6,1,0" data-index-in-node="55">automatically skips</b> tasks already marked as done.</p></li>	
	<li><p data-path-to-node="6,2,0"><b data-path-to-node="6,2,0" data-index-in-node="0">Task Reordering</b>: Includes "Move Up" and "Move Down" buttons so you can easily adjust the priority of your render queue.</p></li>	
	<li><p data-path-to-node="6,3,0"><b data-path-to-node="6,3,0" data-index-in-node="0">Reset Function</b>: You can clear all completion flags with one click to re-run the entire batch.</p></li></ul>

<h3 data-path-to-node="7">3. Interface &amp; Workflow</h3>
<ul data-path-to-node="8">
	<li><p data-path-to-node="8,1,0"><b data-path-to-node="8,1,0" data-index-in-node="0">Progress Tracking</b>: Displays a progress percentage and shows exactly which task is currently being processed.</p></li>
	<li><p data-path-to-node="8,2,0"><b data-path-to-node="8,2,0" data-index-in-node="0">Quick Access</b>: Includes a dedicated button to open the render output folder directly from the panel.</p></li></ul>
<hr data-path-to-node="9">

<h3 data-path-to-node="10">How to Use</h3>
<ol start="1" data-path-to-node="11">
	<li><p data-path-to-node="11,0,0">Locate the <b data-path-to-node="11,0,0" data-index-in-node="11"><code data-path-to-node="11,0,0" data-index-in-node="11">VLRender</code></b> tab in the Sidebar (<b data-path-to-node="11,0,0" data-index-in-node="40">N-Panel</b>) of the 3D Viewport.</p></li>
	<li><p data-path-to-node="11,1,0">Click <b data-path-to-node="11,1,0" data-index-in-node="6">"Add New Task"</b> to create a job.</p></li><li><p data-path-to-node="11,2,0">Assign the desired <b data-path-to-node="11,2,0" data-index-in-node="19">View Layer</b>, <b data-path-to-node="11,2,0" data-index-in-node="31">Camera</b>, and <b data-path-to-node="11,2,0" data-index-in-node="43">Frame Range</b> for that job.</p></li>
	<li><p data-path-to-node="11,3,0">Ensure an output path is set in the standard Blender Render Properties, then click <b data-path-to-node="11,3,0" data-index-in-node="83">"Start Batch Render"</b>.
	</div>
