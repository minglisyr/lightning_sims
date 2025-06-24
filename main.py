import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.widgets import Button

# Clamp function to keep points within the canvas
def clamp(val, minval, maxval):
    return max(minval, min(val, maxval))

# Lightning generation with clamping
def generate_lightning(x1, y1, x2, y2, displace, detail, segs, xlim, ylim):
    if displace < detail:
        segs.append(((x1, y1), (x2, y2)))
    else:
        mid_x = (x1 + x2) / 2 + (np.random.rand() - 0.5) * displace
        mid_y = (y1 + y2) / 2 + (np.random.rand() - 0.5) * displace
        # Clamp midpoints to canvas
        mid_x = clamp(mid_x, xlim[0], xlim[1])
        mid_y = clamp(mid_y, ylim[0], ylim[1])
        generate_lightning(x1, y1, mid_x, mid_y, displace / 2, detail, segs, xlim, ylim)
        generate_lightning(mid_x, mid_y, x2, y2, displace / 2, detail, segs, xlim, ylim)
        # Randomly add a branch
        if np.random.rand() > 0.7 and displace > 10:
            branch_angle = np.pi / 4 * (np.random.rand() - 0.5)
            branch_length = displace * (0.5 + np.random.rand() * 0.5)
            branch_x = mid_x + branch_length * np.cos(branch_angle)
            branch_y = mid_y + branch_length * np.sin(branch_angle)
            branch_x = clamp(branch_x, xlim[0], xlim[1])
            branch_y = clamp(branch_y, ylim[0], ylim[1])
            generate_lightning(mid_x, mid_y, branch_x, branch_y, displace / 2, detail, segs, xlim, ylim)

# Canvas limits
xlim = (-80, 80)
ylim = (0, 110)

# Prepare color gradient (green to red)
cmap = LinearSegmentedColormap.from_list("green_red", ["green", "red"])

plt.style.use('dark_background')
fig, ax = plt.subplots(figsize=(6, 8))
plt.subplots_adjust(bottom=0.15)  # Make space for button
ax.set_xlim(xlim)
ax.set_ylim(ylim)
ax.axis('off')

# Add button
button_ax = plt.axes([0.4, 0.03, 0.2, 0.07])  # x, y, width, height
regen_button = Button(button_ax, 'Regenerate', color='gray', hovercolor='lightgray')

# Placeholders (will be set in regenerate)
lines = []
segments = []
start_marker = None
end_marker = None
ani = None

def regenerate(event=None):
    global lines, segments, start_marker, end_marker, ani

    # Clear previous lines and markers
    for line in lines:
        line.remove()
    lines = []
    if start_marker is not None:
        start_marker.remove()
    if end_marker is not None:
        end_marker.remove()

    # Generate new random start and end points
    start_x = np.random.uniform(xlim[0], xlim[1])
    start_y = ylim[1]
    end_x = np.random.uniform(xlim[0], xlim[1])
    end_y = ylim[0]

    # Generate new lightning segments
    segments.clear()
    generate_lightning(start_x, start_y, end_x, end_y, 80, 2, segments, xlim, ylim)

    # Plot new start and end points
    start_marker, = ax.plot([start_x], [start_y], 'go', markersize=10)
    end_marker, = ax.plot([end_x], [end_y], 'ro', markersize=10)

    # Prepare new lines for animation
    for i, seg in enumerate(segments):
        color_pos = i / (len(segments) - 1) if len(segments) > 1 else 0
        color = cmap(color_pos)
        line, = ax.plot([], [], color=color, linewidth=2)
        lines.append(line)

    def init():
        for line in lines:
            line.set_data([], [])
        return lines

    def update(frame):
        for i, line in enumerate(lines):
            if i <= frame:
                (x1, y1), (x2, y2) = segments[i]
                line.set_data([x1, x2], [y1, y2])
            else:
                line.set_data([], [])
        return lines

    # Remove previous animation if any
    if ani is not None and ani.event_source is not None:
        ani.event_source.stop()
        
    ani = FuncAnimation(fig, update, frames=len(segments), init_func=init,
                        interval=30, blit=True, repeat=False)
    fig.canvas.draw_idle()

# Connect the button
regen_button.on_clicked(regenerate)

# Initial draw
regenerate()

plt.show()
