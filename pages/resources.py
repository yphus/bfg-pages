
from google.appengine.api import images 
from google.appengine.ext import db

from pages.models import NonContentishMixin
import copy
from pickle import loads, dumps

# RawFile and RawImage will always be created with an ancestor

class RawFile(db.Model):
    name= db.StringProperty(required=True)
    mimetype=db.StringProperty(default='application/octet-stream')
    filename=db.StringProperty(default='')
    size=db.IntegerProperty(default=0)
    file=db.BlobProperty()


class RawImage(RawFile):
    width=db.IntegerProperty(default=0)
    height=db.IntegerProperty(default=0)
    
    
class FileResource(NonContentishMixin):
    
    _resource_type = RawFile
    _resource_summary = {'name':'','mimetype':'application/octet-stream','size':0,'filename':''}
    
    default_resource = db.StringProperty()
    filename = db.StringProperty(default="")
    resources_ = db.BlobProperty(default=None) # this is a summary list of the all raw files it holds
                                               #[ {'name':... , 'mimetype':..., 'size':0}, ...]                                        
    
    def _updateOne(self,name,mimetype,resourceobj,filename=""):
        obj = self._updateResource(name,mimetype,resourceobj,filename)
        update_self = self._updateSummary(obj)
        
        obj.put()
        #if update_self:
            #self.resources = self.resources
        self._setResources(self.resources)
        self.put()
    
    def get_resource(self,name):
        if name in self.resources:
            return self._resource_type.get_by_key_name(name,parent=self)
        else:
            raise KeyError("named resource not found (%s)" % name)
    
    def __getitem__(self,name):
        return self.get_resource(name)
    
    def __contains__(self,name):
        if name in self.resources:
            return True
        else:
            return False
    
    def _getResources(self):
##        from gae.utils import BREAKPOINT
##        BREAKPOINT()
        res = getattr(self,'_v_resources_',None)
        if res is None:
            val = {}
            if self.resources_:
                val = loads(self.resources_)
                
            setattr(self,'_v_resources_',val)
            
        
        return self._v_resources_
    
    def _setResources(self,val):
        self.resources_ =  db.Blob(dumps(val))
    
    resources = property(_getResources,_setResources)    
    
    def _updateResource(self,name,mimetype,resourceobj,filename=""):
        if filename=="":
            filename = self.filename
            
        new_key = db.Key.from_path(self._resource_type.kind(),name,parent=self.key())
        obj = db.get(new_key)
        if not obj:
            obj = self._resource_type(parent=self,key_name=name,name=name)

        obj.mimetype = mimetype
        obj.file = db.Blob(resourceobj)
        obj.size = len(resourceobj)
        obj.filename = filename
            
        return obj    

    def _updateSummary(self,obj):
        summary = self.resources.get(obj.name,copy.copy(self._resource_summary))
        
        update_self = False
        
        for key in summary.keys():
            summary[key] = getattr(obj,key)
            
        if summary != self.resources.get(obj.name,copy.copy(self._resource_summary)):
            self.resources[obj.name] = summary
            udate_self = True

    def addFile(self,name,mimetype,resourceobj,filename=''):
        db.run_in_transaction(self._updateOne,name,mimetype,resourceobj,filename)
            
                                              
class ImageResource(FileResource):
    
    """ the resources list holds  [ {'name':... , 'mimetype':..., 'size':0, width: 0, height: 0} ] """
    
    _resource_type = RawImage
    _resource_summary = {'name':'','mimetype':'application/octet-stream','size':0,'width':0,'height':0,'filename':''}
    
    def _updateResource(self,name,mimetype,resourceobj,filename=''):
        image = images.Image(resourceobj)
        obj = super(ImageResource,self)._updateResource(name,mimetype,resourceobj,filename=filename)
        obj.width = image.width
        obj.height = image.height
        return obj
        
    def addImage(self,name,mimetype,resourceobj,filename=''):
           
        db.run_in_transaction(self._updateOne,name,mimetype,resourceobj,filename)
        
    