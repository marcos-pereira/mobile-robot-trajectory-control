--   This code is distributed WITHOUT ANY WARRANTY, without the implied
--   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
--   See the GNU Lesser General Public License for more details.
--
-- Contributors:
-- marcos-pereira (https://github.com/marcos-pereira)

-- Customization hook of CoppeliaSim's "Visualization stream" add-on: the add-on
-- does require 'threejsFrontend-custom' and inserts extraHTML into the viewer page
-- right after threejsFrontend.js. The script it loads is served by the add-on from
-- the CoppeliaSim directory, next to threejsFrontend.js.
return {
    extraHTML = '<script src="threejsFrontend-fixes.js"></script>',
}
