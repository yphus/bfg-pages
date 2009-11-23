from repoze.bfg import testing as bfg_reg
import logging

import interfaces
import views
import schema
from gae.utils import BREAKPOINT

bfg_reg.registerView("@tmp",view=views.fileupload_cache_view)
bfg_reg.registerView("edit",view=views.edit_view)
bfg_reg.registerView("add",view=views.add_view)
bfg_reg.registerView("delete_content",view=views.delete_content,for_=(interfaces.IContent))
bfg_reg.registerView("delete_content", view=views.delete_content,for_=(interfaces.IFolder)) 

bfg_reg.registerAdapter(schema.FolderStructure,(interfaces.IFolder),schema.IStructure)
bfg_reg.registerAdapter(schema.RootStructure,(interfaces.IRoot),schema.IStructure)
bfg_reg.registerAdapter(schema.PageStructure,(interfaces.IPage),schema.IStructure)
bfg_reg.registerAdapter(schema.NewsStructure,(interfaces.INews),schema.IStructure)
bfg_reg.registerAdapter(schema.FileStructure,(interfaces.IFile),schema.IStructure)
bfg_reg.registerAdapter(schema.ImageStructure,(interfaces.IImage),schema.IStructure)
bfg_reg.registerAdapter(schema.PicassaGalleryStructure,(interfaces.IPicassaGallery),schema.IStructure)
bfg_reg.registerAdapter(schema.StaticListStructure,(interfaces.IStaticListView),schema.IStructure)
bfg_reg.registerAdapter(schema.QueryViewStructure,(interfaces.IQueryView),schema.IStructure)
bfg_reg.registerAdapter(schema.ActionStructure,(interfaces.IAction),schema.IStructure)
bfg_reg.registerAdapter(schema.PortletStructure,(interfaces.IPortlet),schema.IStructure)
logging.info('Editing registered')