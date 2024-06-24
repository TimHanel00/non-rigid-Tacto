import os
import multiprocessing
import traceback

from core.pipeline_block import PipelineBlock
from core.log import Log
from core.exceptions import SampleProcessingException
from utils.vtkutils import calc_mesh_size

import gmsh
import contextlib, io

class GmshMeshingBlock(PipelineBlock):

    def __init__(
            self,
            input_filename: str ="surface.stl",
            output_filename: str ="volume.vtk",
            max_time_before_timeout: int = 10 # in seconds
        ):
        inputs = [input_filename]
        outputs = [output_filename]
        self.output_filename = output_filename
        self.input_filename = input_filename
        self.max_time_before_timeout = max_time_before_timeout   # in seconds
        super().__init__(inputs, outputs)

    def run(self, sample):

        gmsh.initialize()
        #gmsh.option.setNumber("General.Verbosity", 0)
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.logger.start()

        try:
            #self.mesh(sample, self.input_filename, self.output_filename) 
            args = (sample, self.input_filename, self.output_filename)
            p = ExceptionSafeProcess(target=self.mesh, args=args)
            p.start()

            p.join(self.max_time_before_timeout)

            # If thread is still active
            if p.is_alive():
            
                # Terminate - may not work if process is stuck for good
                p.terminate()
                # OR Kill - will work for sure, no chance for process to finish nicely however
                # p.kill()
                p.join()

                raise Exception(f"GMSH timed out (waited for {self.max_time_before_timeout} seconds)")
            exception = p.exception
            if exception:
                trace = ""
                for i, e in enumerate(exception):
                    trace += "\t" + str(e)
                raise Exception(f"GMSH failed to run. Exception:\n" + trace )
            elif p.exitcode != 0:
                raise Exception(f"GMSH failed to run, unknown issue")


        except Exception as e:
            logs = gmsh.logger.get()
            sample.write_log( logs )

            # Get traceback:
            #t = ''.join(traceback.format_tb(e.__traceback__))

            gmsh.logger.stop()
            gmsh.finalize()
            raise SampleProcessingException(self, sample,
                    f"Failed to mesh sample, error was: {e}")

        logs = gmsh.logger.get() # TODO: Do something with the logs!

        sample.write_log( logs )

        gmsh.logger.stop()
        gmsh.finalize()
        
    def mesh(self, sample, input_filename, output_filename):

        # Find all files 
        input_filenames = sample.find_matching_files(input_filename)
        assert len(input_filenames) > 0, \
                f"Found no filenames matching '{input_filename}', cannot mesh!"
        assert len(input_filenames) == 1, \
                f"Found multiple filenames matching '{input_filename}', don't know which to mesh! Consider making the pattern more specific, or and maybe using multiple GmshMeshingBlocks."

        # Because we want gmsh to open the files, make sure it's saved to disk:
        sample.flush_data(filenames=input_filenames)

        meshes = list(sample.read_all(input_filename))
        mesh = meshes[0][1]
        # preoperative number of points on surface
        num_points = mesh.GetNumberOfPoints()
        sample.add_statistic(self, "preop_surface_num_points", num_points)

        for filename in input_filenames:

            full_filename = os.path.join(sample.path, filename)
            gmsh.open(full_filename)

            # This is how you set options for gmsh:
            # TODO: Make these configurable!
            gmsh.option.setNumber("Mesh.CharacteristicLengthMax", 0.01)

            # Print the model name and dimension:
            #print('Model ' + gmsh.model.getCurrent() + ' (' +
            #    str(gmsh.model.getDimension()) + 'D)')

            n = gmsh.model.getDimension()
            s = gmsh.model.getEntities(n)
            l = gmsh.model.geo.addSurfaceLoop([s[i][1] for i in range(len(s))])
            gmsh.model.geo.addVolume([l])
            gmsh.model.geo.synchronize()

            gmsh.model.mesh.generate(dim=3)
            gmsh.model.mesh.optimize(method="Netgen", force=True)

            # Print the model name and dimension:
            #print('Model ' + gmsh.model.getCurrent() + ' (' +
            #    str(gmsh.model.getDimension()) + 'D)')

            output_fname = os.path.join(sample.path, output_filename)
            gmsh.write(output_fname)

            # We can use this to clear all the model data:
            #gmsh.clear()

        # the previous loop should only run once, otherwise still only produces one output
        meshes = list(sample.read_all(output_filename))
        assert len(meshes) > 0, f"Generation of {output_filename} by GmshMeshingBlock failed"
        assert len(meshes) <= 1, f"Too many files matching {output_filename} produced by GmshMeshingBlock"
        mesh = meshes[0][1]
        # preoperative number of points
        num_points = mesh.GetNumberOfPoints()
        sample.add_statistic(self, "preop_volume_num_points", num_points)
        # dimension/size of preoperative object
        size_x, size_y, size_z = calc_mesh_size(mesh)
        sample.add_statistic(self, "preop_volume_size_x", size_x)
        sample.add_statistic(self, "preop_volume_size_y", size_y)
        sample.add_statistic(self, "preop_volume_size_z", size_z)


class ExceptionSafeProcess(multiprocessing.Process):
    def __init__(self, *args, **kwargs):
        multiprocessing.Process.__init__(self, *args, **kwargs)
        self._pconn, self._cconn = multiprocessing.Pipe()
        self._exception = None

    def run(self):
        try:
            multiprocessing.Process.run(self)
            self._cconn.send(None)
        except Exception as e:
            tb = traceback.format_exc()
            self._cconn.send((e, tb))

    @property
    def exception(self):
        if self._pconn.poll():
            self._exception = self._pconn.recv()
        return self._exception


