import pygame
from OpenGL.GL import *
import OpenGL.GL.shaders as shaders
import glm
import pyassimp
import numpy
import math

class Render: 
    def viewport_dimensions(self): 
        self.viewport_height = 920
        self.viewport_width = 1080
    
    def init_pygame(self): 
        pygame.init()
        pygame.display.set_mode(
            (self.viewport_width, self.viewport_height), 
            pygame.OPENGL | pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        pygame.key.set_repeat(1, 10)
        
        glClearColor(0.15, 0.10, 0.20, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_TEXTURE_2D)
        
    def get_shader(self):
        self.vertex_shader = open('data/shaders/vertex_shader.shader', 'r').read()
        self.fragment_shader = open('data/shaders/fragment_shader.shader', 'r').read()
        self.active_shader = shaders.compileProgram(
            shaders.compileShader(self.vertex_shader, GL_VERTEX_SHADER),
            shaders.compileShader(self.fragment_shader, GL_FRAGMENT_SHADER),
        )
        glUseProgram(self.active_shader)

    def get_matrixes(self): 
        angle = 45
        self.model = glm.mat4(1)
        self.view = glm.mat4(1)
        self.projection = glm.perspective(
            glm.radians(angle), 
            self.viewport_width/self.viewport_height, 
            0.1, 
            1000.0
        )
        glViewport(
            0, 
            0, 
            self.viewport_width, 
            self.viewport_height
        )

    def open_file(self): 
        self.scene = pyassimp.load('./models/OBJ/castle.obj')
    
    def select_texture(self, num): 
        if num == 1: 
            texture = "./models/OBJ/textures/Haus_C.jpg"
        elif num == 2: 
            texture = "./models/OBJ/textures/Haus_N.jpg"
        else: 
            texture = "./models/OBJ/textures/Haus_S.jpg"

        return texture 

    def gl_apply_render(self, node, type_texture):
        self.model = node.transformation.astype(numpy.float32)
        
        for mesh in node.meshes:

            texture_surface = pygame.image.load(self.select_texture(type_texture))
            texture_data = pygame.image.tostring(texture_surface,"RGB",1)
            
            width = texture_surface.get_width()
            height = texture_surface.get_height()
            
            texture = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, texture)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, texture_data)
            glGenerateMipmap(GL_TEXTURE_2D)
            
            vertex_data = numpy.hstack((
                numpy.array(mesh.vertices, dtype=numpy.float32),
                numpy.array(mesh.normals, dtype=numpy.float32),
                numpy.array(mesh.texturecoords[0], dtype=numpy.float32)
            ))
            
            faces = numpy.hstack(
                numpy.array(mesh.faces, dtype=numpy.int32)
            )

            diffuse = mesh.material.properties["diffuse"]

            self.gl_lashing(vertex_data,faces)
            self.matrices_lashing(diffuse)
            glDrawElements(
                GL_TRIANGLES, 
                len(faces), 
                GL_UNSIGNED_INT, 
                None
            )

        for child in node.children:
            self.gl_apply_render(child, type_texture)

    def gl_lashing(self, vertex_data, faces): 
        
        vertex_buffer_object = glGenVertexArrays(1)
        glBindBuffer(GL_ARRAY_BUFFER, vertex_buffer_object)
        glBufferData(GL_ARRAY_BUFFER, vertex_data.nbytes, vertex_data, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 3, GL_FLOAT, False, 9 * 4, None)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 3, GL_FLOAT, False, 9 * 4, ctypes.c_void_p(3 * 4))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 3, GL_FLOAT, False, 9 * 4, ctypes.c_void_p(6 * 4))
        glEnableVertexAttribArray(2)

        element_buffer_object = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, element_buffer_object)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, faces.nbytes, faces, GL_STATIC_DRAW)

    def matrices_lashing(self, diffuse): 
        glUniformMatrix4fv(
            glGetUniformLocation(self.active_shader, "model"), 
            1 , 
            GL_FALSE, 
            self.model
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.active_shader, "view"), 
            1 , 
            GL_FALSE, 
            glm.value_ptr(self.view)
        )
        glUniformMatrix4fv(
            glGetUniformLocation(self.active_shader, "projection"), 
            1 , 
            GL_FALSE, 
            glm.value_ptr(self.projection)
        )
        glUniform4f(
            glGetUniformLocation(self.active_shader, "color"),
            *diffuse,
            1
        )
        glUniform4f(
            glGetUniformLocation(self.active_shader, "light"), 
            -150, 
            150, 
            160, 
            1
        )

    def set_camera(self): 
        self.camera = glm.vec3(0, 100, 180)
        self.camera_speed = 180  
        self.angle = 0

    def process_input(self, angle, camera_speed, type_tex):
        constant = 0.08 
        self.angle = angle 
        self.camera_speed = camera_speed
        type_tex = 1
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                return True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.angle = self.angle - constant 
                    self.camera.x = self.camera_speed*math.cos(self.angle)
                    self.camera.z = self.camera_speed*math.sin(self.angle) 
                if event.key == pygame.K_RIGHT:
                    self.angle = self.angle + constant 
                    self.camera.x = self.camera_speed*math.cos(self.angle)
                    self.camera.z = self.camera_speed*math.sin(self.angle)
                if event.key == pygame.K_UP: 
                    if (self.camera_speed<= 160): 
                        self.camera_speed = 160
                    else: 
                        self.camera_speed = self.camera_speed - 10 
                        self.camera.x = self.camera_speed*math.cos(self.angle)
                        self.camera.z = self.camera_speed*math.sin(self.angle)
                        print(self.camera_speed)
        
                if event.key == pygame.K_DOWN: 
                    if (self.camera_speed >= 500): 
                        self.camera_speed = 500 
                    else: 
                        self.camera_speed = self.camera_speed + 10 
                        self.camera.x = self.camera_speed*math.cos(self.angle)
                        self.camera.z = self.camera_speed*math.sin(self.angle)
                if event.key == pygame.K_a: 
                    type_tex = 2 
                if event.key == pygame.K_s: 
                    type_tex = 3 

                        

                
            
        return False, self.angle, self.camera_speed, type_tex

if __name__ == '__main__': 
    render = Render()
    render.viewport_dimensions()
    render.init_pygame()
    render.get_shader()
    render.get_matrixes()
    render.open_file()
    render.set_camera()
    
    done = False
    render_angle = 0 
    render_speed = 180
    new_texture = 1
    
    while not done:
        glClear(
            GL_COLOR_BUFFER_BIT | 
            GL_DEPTH_BUFFER_BIT
        )
        
        render.view = glm.lookAt(
        render.camera, 
        glm.vec3(0, 0, 0), 
        glm.vec3(0, 1, 0)
        )
    
        render.gl_apply_render(
             render.scene.rootnode, 
             type_texture = new_texture
        )

        done, render_angle, render_speed, new_texture = render.process_input(
            render_angle, 
            render_speed, 
            new_texture
        )

        render.clock.tick(15)
        pygame.display.flip()