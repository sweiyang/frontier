import os

class Frontend:
    BUILD_DIR_NAME = "dist"
    
    def __init__(self):
        # core/frontend/../.. -> conduit root
        self.root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
        self.frontend_dir = os.path.join(self.root_dir, "frontend")
        self.build_dir = os.path.join(self.frontend_dir, self.BUILD_DIR_NAME)
        
    def get_build_dir(self) -> str:
        """Returns the absolute path to the frontend build directory."""
        if not os.path.exists(self.build_dir):
            # Fallback or warning could go here. For now just return the path.
            pass 
        return self.build_dir
    
    def get_index_html(self) -> str:
        """Returns the absolute path to the index.html file."""
        return os.path.join(self.build_dir, "index.html")