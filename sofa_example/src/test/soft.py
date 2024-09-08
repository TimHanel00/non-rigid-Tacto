constraint = self.rootNode.Cube.collision.MechanicalObject.constraint.value
dt = self.rootNode.dt.value
constraintMatrixInline = np.fromstring(constraint, sep='  ')

pointId = []
constraintId = []
constraintDirections = []
index = 0
i = 0

forcesNorm = self.rootNode.GCS.constraintForces.value
contactforce_x = 0
contactforce_y = 0
contactforce_z = 0

while index < len(constraintMatrixInline):
    nbConstraint   = int(constraintMatrixInline[index+1])
    currConstraintID = int(constraintMatrixInline[index])
    for pts in range(nbConstraint):
        currIDX = index+2+pts*4
        pointId = np.append(pointId, constraintMatrixInline[currIDX])
        constraintId.append(currConstraintID)
        constraintDirections.append([constraintMatrixInline[currIDX+1],constraintMatrixInline[currIDX+2],constraintMatrixInline[currIDX+3]])
    index = index + 2 + nbConstraint*4

nbDofs = len(self.rootNode.Cube.collision.MechanicalObject.position.value)
forces = np.zeros((nbDofs,3))


print('pointid', pointId)
print('constraintId', constraintId)


for i in range(len(pointId)):
    indice = int(pointId[i])
    forces[indice][0] = forces[indice][0] + constraintDirections[i][0] * forcesNorm[constraintId[i]] / dt
    forces[indice][1] = forces[indice][1] + constraintDirections[i][1] * forcesNorm[constraintId[i]] / dt
    forces[indice][2] = forces[indice][2] + constraintDirections[i][2] * forcesNorm[constraintId[i]] / dt

    print('indice', i, indice)

for i in range (nbDofs):
    contactforce_x += forces[i][0]
    contactforce_y += forces[i][1]
    contactforce_z += forces[i][2]


print('nbDof', nbDofs)
print('force', forces)
print('contactforce', contactforce_x, contactforce_y, contactforce_z)

if len(constraintMatrixInline) > 0:
    self.rootNode.drawNode.drawForceFF.indices.value = list(range(0,nbDofs,1))
    self.rootNode.drawNode.drawForceFF.forces.value = forces
    self.rootNode.drawNode.drawPositions.position.value = self.rootNode.Cube.collision.MechanicalObject.position.value