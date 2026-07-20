from pathlib import Path
import open3d as o3d


class ModelRenderer:

    def __init__(self, project_dir):

        self.project_dir = Path(project_dir)

        self.model_path = self.project_dir / "model.glb"

        self.output_dir = self.project_dir / "screenshots"

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self):

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model not found: {self.model_path}"
            )

        mesh = o3d.io.read_triangle_mesh(str(self.model_path))

        if mesh.is_empty():
            raise RuntimeError("Mesh is empty.")

        mesh.compute_vertex_normals()

        try:

            vis = o3d.visualization.Visualizer()

            vis.create_window(
                width=1600,
                height=900,
                visible=False,
            )

            vis.add_geometry(mesh)

            opt = vis.get_render_option()

            opt.mesh_show_back_face = True

            ctr = vis.get_view_control()

            # ---------------- Front ----------------

            ctr.set_front([0, 0, -1])

            ctr.set_up([0, -1, 0])

            ctr.set_zoom(0.75)

            vis.poll_events()

            vis.update_renderer()

            vis.capture_screen_image(
                str(self.output_dir / "front.png"),
                True,
            )

            # ---------------- Top ----------------

            ctr.set_front([0, -1, 0])

            ctr.set_up([0, 0, -1])

            vis.poll_events()

            vis.update_renderer()

            vis.capture_screen_image(
                str(self.output_dir / "top.png"),
                True,
            )

            # ---------------- ISO ----------------

            ctr.set_front([0.7, -0.5, -0.6])

            ctr.set_up([0, -1, 0])

            vis.poll_events()

            vis.update_renderer()

            vis.capture_screen_image(
                str(self.output_dir / "iso.png"),
                True,
            )

            vis.destroy_window()

            return True

        except Exception as e:

            print("=" * 60)
            print("WARNING")
            print("Automatic screenshot generation failed.")
            print("PDF will still be generated.")
            print(e)
            print("=" * 60)

            return False