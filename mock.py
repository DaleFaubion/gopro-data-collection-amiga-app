#

import numpy as np
import matplotlib.pyplot as plt

from tests.mocks.file_org import mock_locations


locs = mock_locations(21, 21, 5, "SE").reset_index()
locs["color"] = (locs["row"] == 5).astype(np.uint8)
locs.plot(kind="scatter", x="lat", y="lon", c="color", colormap="viridis")
plt.show()

locs["dlon"] = np.gradient(locs["lon"])
locs["color"] = locs["dlon"]
locs.plot(kind="scatter", x="lat", y="lon", c="color", colormap="jet")
plt.show()

locs["color"] = (locs["bay"] == 5).astype(np.uint8)
locs.plot(kind="scatter", x="lat", y="lon", c="color", colormap="viridis")
plt.show()
