//   This code is distributed WITHOUT ANY WARRANTY, without the implied
//   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
//   See the GNU Lesser General Public License for more details.
//
// Contributors:
// marcos-pereira (https://github.com/marcos-pereira)

// Fixes for CoppeliaSim's Three.js viewer (threejsFrontend.js), injected into the
// page by threejsFrontend-custom.lua right after threejsFrontend.js is loaded.
//
// Coplanar meshes of a compound shape z-fight in Three.js. Example: each tile of
// the ResizableFloor is a compound of two textured checker meshes plus a black
// base quad, all at z = 0. CoppeliaSim's own renderer draws a compound's meshes in
// order and the first one wins on equal depth, so the black quad stays hidden
// behind the tiles. Three.js resolves the tie per pixel instead, which shows up as
// black patches all over the floor. Pushing every later mesh of a compound slightly
// back in depth (polygon offset) reproduces CoppeliaSim's order.
(function () {
    if (typeof Mesh === 'undefined' || !Mesh.prototype.update) {
        console.warn('threejsFrontend-fixes: Mesh class not found, compound depth fix not applied.');
        return;
    }

    const originalUpdate = Mesh.prototype.update;

    // Push the mesh back in depth according to its position in the shape's mesh list
    function applyCompoundDepthOrder(meshObject) {
        const shape = meshObject.parent;
        const meshUids = shape && shape.userData ? shape.userData.meshes : undefined;
        if (!Array.isArray(meshUids)) return;
        const meshIndex = meshUids.indexOf(meshObject.userData.uid);
        if (meshIndex <= 0) return;
        const material = meshObject.mesh.material;
        // threejsFrontend.js uses factor 0.5 / units 0 for every mesh
        material.polygonOffset = true;
        material.polygonOffsetFactor = 0.5 + meshIndex;
        material.polygonOffsetUnits = 4 * meshIndex;
        material.needsUpdate = true;
    }

    Mesh.prototype.update = function (eventData) {
        originalUpdate.call(this, eventData);
        applyCompoundDepthOrder(this);
    };
})();
