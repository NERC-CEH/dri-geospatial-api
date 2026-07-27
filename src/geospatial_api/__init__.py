import warnings

warnings.filterwarnings("ignore")

# importing after filter the warnings to ensure that deprecation issues dont get
# logged before we have imported the JSON logger.
import autosemver  # noqa: E402

try:
    __version__ = autosemver.packaging.get_current_version(project_name="geospatial_api")
except Exception:
    __version__ = "0.0.0"
