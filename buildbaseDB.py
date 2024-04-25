import pickle
from hashlib import *
import datetime
import os
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.orderinglist import ordering_list
from sqlalchemy.orm import relationship, Session, with_polymorphic,  backref
import shutil

Base = declarative_base()

Users_Groups = Table('users_groups', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('group_id', Integer, ForeignKey('user_group.id')) )

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    user_username = Column(String(32))
    user_first_name = Column(String(32))
    user_last_name = Column(String(32))
    user_pass_hash = Column(String(600))
    user_post_title = Column(String(600))
    user_active = Column(Boolean)
    user_system = Column(Boolean)

    user_groups = relationship("UserGroup", secondary=Users_Groups, backref='group_users')

    def __init__(self, user_username, user_first_name, user_last_name):
        self.user_username = user_username
        self.user_first_name = user_first_name
        self.user_last_name = user_last_name

    def __repr__(self):
        return "User('%s', '%s', '%s')" % (self.user_username, self.user_first_name, self.user_last_name)

    def __str__(self):
        return "<User -- %s >" % (self.user_username)

    def auth(self, user_hash, key):
        return (user_hash == sha512((self.user_pass_hash+key).encode()).hexdigest()) if key else False

    def __eq__(self, other):
        return (other == self.id) if type(other) is int else (other == self.user_username)

    def hasCtlProp(self, ctl_prop):
        isin = False
        for group in self.user_groups:
            if group.hasCtlProp(ctl_prop) == '_DENY_':
                return False
            elif group.hasCtlProp(ctl_prop) == '_ALOW_':
                isin = True
        return isin



Group_Ctl = Table('group_ctl', Base.metadata,
    Column('group_id', ForeignKey('user_group.id'), primary_key=True),
    Column('ctl_prop_id', ForeignKey('ctl_prop.id'), primary_key=True) )

Groups_Groups = Table('groups_groups', Base.metadata,
    Column('group_idP', Integer, ForeignKey('user_group.id')),
    Column('group_idC', Integer, ForeignKey('user_group.id')) )

class UserGroup(Base):
    __tablename__ = 'user_group'

    id = Column(Integer, primary_key=True)
    group_name = Column(String(32))
    group_deny = Column(Boolean)        # When true this group will deny any users in it to those ctl_propertys assigned to it.
    group_private = Column(Boolean)     # For use within groups not general viewing
    group_groups_id = Column(Integer, ForeignKey('user_group.id'))  # Parent group, this allows for a hiarchy of groups.
                                                                    # a section of a progam can create there own group that has groups for deferent permitions

    # group_parent = relationship("UserGroup", remote_side=[id], foreign_keys=group_groups_id)
    # group_sub_groups = relationship("UserGroup", foreign_keys=group_groups_id)
    group_sub_groups = relationship("UserGroup", secondary=Groups_Groups,
                                    primaryjoin=id==Groups_Groups.c.group_idP,
                                    secondaryjoin=id==Groups_Groups.c.group_idC,
                                    backref='group_parent')
    group_ctl = relationship("controlProperty", secondary=Group_Ctl, backref='ctl_group')

    def __init__(self, group_name):
        self.group_name = group_name

    def __repr__(self):
        return "UserGroup('%s')" % (self.group_name)

    def __str__(self):
        return "<UserGroup -- %s >" % (self.group_name)

    def __contains__(self, item):
        return item in self.group_users

    def __iter__(self):
        return self.group_users.__iter__()

    def __getitem__(self, item):
        return self.group_users[self.group_users.index(item)] if item in self.group_users else None

    def hasCtlProp(self, ctl_prop):
        isin = '_MABY_'
        if ctl_prop in self.group_ctl and self.group_deny:
            return '_DENY_'
        elif ctl_prop in self.group_ctl:
            isin = '_ALOW_'
        for group in self.group_sub_groups:
            if group.hasCtlProp(ctl_prop) == '_DENY_':
                return '_DENY_'
            elif group.hasCtlProp(ctl_prop) == '_ALOW_':
                isin = '_ALOW_'
        return isin


class controlProperty(Base):
    __tablename__ = 'ctl_prop'

    id = Column(Integer, primary_key=True)
    ctl_title = Column(String(50))

    def __init__(self, ctl_title):
        self.ctl_title = ctl_title

    def __eq__(self, other):
        return (other == self.id) if type(other) is int else (other == self.ctl_title)


class metaData(Base):
    __tablename__ = 'meta_data'

    id = Column(Integer, primary_key=True)
    meta_default_post_id = Column(Integer, ForeignKey('post_data.id'))
    meta_channal = Column(Integer)
    mata_network_BP = Column(Boolean)
    mata_network_stats = Column(Boolean)
    mata_db_version = Column(Integer) # every 100 is a major upgrade
    mata_code_version = Column(Integer) # every 100 is a major upgrade
    meta_options = Column(String(25)) # Settings Flag for everything see options settings file


    meta_default_post = relationship("PostData", foreign_keys=meta_default_post_id)

    def __init__(self):
        self.meta_network_BP = False
        self.meta_network_stats = False
        self.meta_channal = 1
        self.meta_db_version = 150
        self.meta_code_version = 100

    def __repr__(self):
        return "<metaData('%s - %s')>" % (self.meta_default_post, self.meta_channal)

#--------------------------------------------------------------------------------------------------------------------------------#

class State(Base): 
    '''this is the state that the objects are a part of (as-built, construction, planning)
    this should be connected to the objects and the rooms.
    
    '''
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True)
    state_title
    state_discription
    state_notes
    state_pt_state
    state_date
    state_implimented_date
    state_created_date
    state_modified_date
    state_based_on
    state_
    org_post_id = Column(Integer, ForeignKey('post_data.id'))
    list_active = Column(Boolean) # is this an active list (is it still being used)

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class Group(Base): 
    '''this is the state that the objects are a part of (as-built, construction, planning)
    this should be connected to the objects and the rooms.
    
    '''
    __tablename__ = 'group'

    id = Column(Integer, primary_key=True)
    group_title
    group_discription
    sgroup_notes
    group_closed
    group_

    org_post_id = Column(Integer, ForeignKey('post_data.id'))
    list_active = Column(Boolean) # is this an active list (is it still being used)

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class Org(Base):
    __tablename__ = 'org'

    id = Column(Integer, primary_key=True)
    org_post_id = Column(Integer, ForeignKey('post_data.id'))
    org_title = Column(String)
    org_name = Column(String(30))
    org_full_name = Column(String(100))
    org_abbr = Column(String(30))
    org_primary_building = Column(Integer, ForeignKey('building.id'))

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class Site(Base):
    __tablename__ = 'site'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))
    site_name
    list_active = Column(Boolean) # is this an active list (is it still being used)

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class Building(Base):
    __tablename__ = 'building'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))
    list_active = Column(Boolean) # is this an active list (is it still being used)
    building_org_id = Column(Integer, ForeignKey('org.id'))

    building_name = Column(String(100)) # what is the name of the building(may not be the same as the org)
    building_date = Column(DateTime()) # when did the building come on our line
    building_pt_new = Column(Boolean) # Is this a PT building that the org is renovating/using
    building_description = Column(String(500)) # A description of the building/what it is for what is in it, etc.
    building_ideal = Column(Boolean)

    building_sqft = Column(Integer)
    building_floors = Column(Integer)
    building_hight = Column(Integer)
    building_purchased_date = Column(DateTime())
    building_constructed_date = Column(DateTime())

    address_street = Column(Unicode(200, collation='utf8_bin'))
    address_zip = Column(String(100))
    address_city_id = Column(Integer, ForeignKey('city.id'))
    address_country_id = Column(Integer, ForeignKey('country.id'))
    address_long = Column(Float)
    address_lat = Column(Float)

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class Floor(Base):
    __tablename__ = 'floor'

    id = Column(Integer, primary_key=True)
    floor_building
    floor_name
    floor_order

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class Room(Base):
    __tablename__ = 'room'

    id = Column(Integer, primary_key=True)
    space_floor = Column(Integer)
    space_titles = Column()
    space_sqpcs


    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id


class ColumnObject(Base):
    __tablename__ = 'column_object'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))

    wall_height = Column(Integer)
    wall_width = Column(Integer)
    wall_depth = Column(Integer)
    wall_position = Column(JSON)
    wall_rotation = Column(JSON)

    wall_building = Column(Integer, ForeignKey('post_data.id'))
    wall_group = Column(Integer, ForeignKey('post_data.id'))
    wall_state = Column(Integer, ForeignKey('post_data.id'))
    wall_site = Column(Integer, ForeignKey('post_data.id'))

    wall_baseboard = Column(Boolean)
    wall_crown = Column(Boolean)
    wall_points = Column(JSON)

    wall_properties = Column(JSON)
    wall_notes = Column(String(100))
    wall_created = Column(DateTime())
    wall_modified = Column(DateTime())

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id


class WallObject(Base):
    __tablename__ = 'wall_object'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))

    wall_start_height = Column(Integer)
    wall_end_height = Column(Integer)
    wall_width = Column(Integer)

    wall_start_wall_id = Column(Integer, ForeignKey('post_data.id'))
    wall_end_wall_id = Column(Integer, ForeignKey('post_data.id'))

    wall_floor = Column(Integer, ForeignKey('post_data.id'))
    wall_group = Column(Integer, ForeignKey('post_data.id'))
    wall_state = Column(Integer, ForeignKey('post_data.id'))
    wall_site = Column(Integer, ForeignKey('post_data.id'))

    wall_baseboard = Column(Boolean)
    wall_crown = Column(Boolean)
    wall_points = Column(JSON)

    wall_properties = Column(JSON)
    wall_notes = Column(String(100))
    wall_created = Column(DateTime())
    wall_modified = Column(DateTime())

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class SysObject(Base):
    __tablename__ = 'sys_object'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))
    list_active = Column(Boolean) # is this an active list (is it still being used)
    list_fields = Column(JSON) # list specific data

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class FFnE(Base):
    __tablename__ = 'object'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))
    list_active = Column(Boolean) # is this an active list (is it still being used)
    list_fields = Column(JSON) # list specific data

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class Object(Base):
    __tablename__ = 'object'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))
    list_active = Column(Boolean) # is this an active list (is it still being used)
    list_fields = Column(JSON) # list specific data

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

class Property(Base):
    __tablename__ = 'property'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))
    list_active = Column(Boolean) # is this an active list (is it still being used)


    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id


#--------------------------------------------------------------------------------------------------------------------------------#
   
class EstatesSit(Base):
    __tablename__ = 'estatesSit'

    id = Column(Integer, primary_key=True)
    estatesSit_building_id = Column(Integer, ForeignKey('building.id'))
    estatesSit_estates_id = Column(Integer, ForeignKey('estates.id'))
    estatesSit_sit = Column(String(100))
    estatesSit_sit_data = Column(String(1000))
    estatesSit_date = Column(DateTime())
    estatesSit_bugs = Column(String(100))
    estatesSit_terminal = Column(String(100))
    estatesSit_status = Column(Integer)
    estatesSit_level = Column(Integer)

    estatesSit_org = relationship("Building", foreign_keys=estatesSit_building_id, backref='building_estates_Sits')
    estatesSit_estates = relationship("Estates", foreign_keys=estatesSit_estates_id)

    def __init__(self, estatesSit_org, estatesSit_estates, estatesSit_sit):
        self.estatesSit_org = estatesSit_org
        self.estatesSit_estates = estatesSit_estates
        self.estatesSit_sit = estatesSit_sit

    def __repr__(self):
        return "<EstatesSit('%s - %s')>" % (self.estatesSit_org, self.estatesSit_sit)

class ListName(Base):
    __tablename__ = 'list_name'

    id = Column(Integer, primary_key=True)
    list_post_id = Column(Integer, ForeignKey('post_data.id'))
    list_active = Column(Boolean) # is this an active list (is it still being used)
    list_pt = Column(Boolean) # the active list right now
    list_in_bp = Column(Boolean) # the active list right now
    list_checklist = Column(Boolean) # Is this a checklist
    list_name = Column(String(50)) # Name of List
    list_abbr = Column(String(10)) # Abbr of List
    list_description = Column(String(500))
    list_fields = Column(JSON) # list specific data

    def __init__(self, list_name, list_post_id):
        self.list_name = list_name
        self.list_post_id = list_post_id

# This is the Many-to-Many Table.
ListRec_Tag = Table('listrec_tag', Base.metadata,
    Column('list_record_id', Integer, ForeignKey('list_record.id')),
    Column('tag_id', Integer, ForeignKey('tag.id')))

# This is the Many-to-Many Table.
Photo_Tag = Table('photo_tag', Base.metadata,
    Column('photo_rec_id', Integer, ForeignKey('photo_rec.id')),
    Column('tag_id', Integer, ForeignKey('tag.id')))

class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    tag_name = Column(String(50)) # Name of List
    tag_abbr = Column(String(10)) # Abbr of List
    tag_post_id = Column(Integer, ForeignKey('post_data.id'))
    tag_description = Column(String(500))
    tag_color = Column(String(8))
    tag_cat = Column(String(8))
    tag_parent_id = Column(Integer, ForeignKey('tag.id')) # categories for the tags to sort them when there are a lot of them.
    tag_is_parent = Column(Boolean) # is this tag used as a parent for other categories
    tag_active = Column(Boolean) # is this tag still in use.
    tag_display = Column(Boolean) # do you want the show this tag.
    tag_from_parent = Column(Boolean) # get the setting from the parent tag.


    tag_parent = relationship("Tag", remote_side=[id], foreign_keys=tag_parent_id)
    #tag_lists = relationship("ListName", secondary=List_Tag, backref='list_tags') # -- tag the item.

    def __init__(self, tag_name, tag_post_id):
        self.tag_name = tag_name
        self.tag_post_id = tag_post_id
        self.tag_from_parent = False
        self.tag_display = True
        self.tag_active = True


class ListRecord(Base):
    __tablename__ = 'list_record'

    id = Column(Integer, primary_key=True)
    listrec_id = Column(Integer) # localized ID
    listrec_list_name_id = Column(Integer, ForeignKey('list_name.id')) # -- what list is this a part of.
    listrec_dateCreated = Column(DateTime())
    listrec_dateModified = Column(DateTime())
    listrec_toBeStartDate = Column(DateTime())# --DB v.150-- When does this target start (not finish)
    listrec_toStartDate = Column(DateTime())
    listrec_toBeDoneDate = Column(DateTime())
    listrec_conditional = Column(Boolean) # -- Need to impliment (command: cond)
    listrec_assignedTo_id = Column(Integer, ForeignKey('post_data.id')) # -- Need to impliment (%)
    listrec_priority = Column(Integer) # -- Need to impliment (command: prio) Basically a sort of the items
    listrec_category = Column(String(50))
    listrec_Item_title = Column(String(50))
    listrec_dependsOn_id = Column(Integer, ForeignKey('list_record.id')) # -- Need to impliment (command: dep)
    listrec_masterTarget_id = Column(Integer, ForeignKey('list_record.id')) 
    listrec_startDate = Column(DateTime())# --DB v.150-- When did this target start
    listrec_doneDate = Column(DateTime())
    listrec_post_id = Column(Integer, ForeignKey('post_data.id'))
    listrec_notes = Column(String(500))
    listrec_description = Column(String(500))
    listrec_handling = Column(String(500))
    listrec_price = Column(Float) # -- what is this going to cost.
    listrec_manhours = Column(Float) # -- what is the man hours to get this done.
    listrec_fields = Column(JSON) # list specific data
    listrec_order = Column(Integer) # Orger of items in the list

    listrec_list_name = relationship("ListName", foreign_keys=listrec_list_name_id, backref='list_name_records')
    listrec_tag = relationship("Tag", secondary=ListRec_Tag, backref='tag_listrec') # -- tag the item.
    listrec_dependsOn = relationship("ListRecord", foreign_keys=listrec_dependsOn_id, remote_side=[id])
    listrec_masterTarget = relationship("ListRecord", foreign_keys=listrec_masterTarget_id, remote_side=[id])
    listrec_post = relationship("PostData", foreign_keys=listrec_post_id)
    listrec_assignedTo = relationship("PostData", foreign_keys=listrec_assignedTo_id)


    def __init__(self, listrec_Item_title, listrec_post):
        self.listrec_Item_title = listrec_Item_title
        self.listrec_post_id = listrec_post

    def __repr__(self):
        return "<ListRecord('%s - %s')>" % (self.listrec_Item_title, self.listrec_toBeDoneDate)


class PhotoCat(Base):
    __tablename__ = 'photo_cat'

    id = Column(Integer, primary_key=True)
    photocat_post_id = Column(Integer, ForeignKey('post_data.id'))
    photocat_active = Column(Boolean) # is this an active list (is it still being used)
    photocat_default = Column(Boolean) # the active list right now
    photocat_shared = Column(Boolean) # is viewable to others
    photocat_name = Column(String(50)) # Name of List
    photocat_description = Column(String(500))
    photocat_opt = Column(JSON) # Photo cat specific options
    photocat_sort_by = Column(Integer) # 0: Date, 1: Tag
    photocat_tag_id = Column(Integer, ForeignKey('tag.id'))
    photocat_filename_rule = Column(String(256)) # Rule for filenames in this cat:
                                                        # %f: Filename
                                                        # %s: Numerical seq
                                                        # %t: Tag
                                                        # %d: Date
                                                        # %l: list_record title


    def __init__(self, photocat_name, photocat_post_id):
        self.photocat_name = photocat_name
        self.photocat_post_id = photocat_post_id


class PhotoRec(Base):
    __tablename__ = 'photo_rec'

    id = Column(Integer, primary_key=True)
    photorec_id = Column(Integer) # localized ID
    photorec_post_id = Column(Integer, ForeignKey('post_data.id'))
    photorec_photocat_id = Column(Integer, ForeignKey('photo_cat.id'))
    photorec_listrec_id = Column(Integer, ForeignKey('list_record.id'))
    photorec_dateCreated = Column(DateTime())
    photorec_dateModified = Column(DateTime())
    photorec_date = Column(DateTime())
    photorec_category = Column(String(50))
    photorec_photo_path = Column(String(512))
    photorec_photo_filename = Column(String(256))
    photorec_photo_original_filename = Column(String(256))
    photorec_photo_type = Column(String(25))
    photorec_photo_title = Column(String(50))
    photorec_photo_size = Column(Integer)
    photorec_photo_height = Column(Integer)
    photorec_photo_width = Column(Integer)
    photorec_notes = Column(String(500))
    photorec_description = Column(String(500))
    photorec_fields = Column(JSON) # Photo reg additional data

    photorec_list = relationship("ListRecord", foreign_keys=photorec_listrec_id, backref='list_record_photos')
    photorec_tag = relationship("Tag", secondary=Photo_Tag, backref='tag_photorec') # -- tag the item.
    #photorec_post = relationship("PostData", foreign_keys=photorec_post_id)


    def __init__(self, photorec_post_id, photorec_photo_path, photorec_photo_filename):
        self.photorec_post_id = photorec_post_id
        self.photorec_photo_path = photorec_photo_path
        self.photorec_photo_filename = photorec_photo_filename

    def __repr__(self):
        return "<PhotoRec('%s - %s')>" % (self.photorec_photo_filename, self.photorec_photo_title)


class CalendarDef(Base):
    __tablename__ = 'calendar_def'

    id = Column(Integer, primary_key=True)
    caldef_dateCreated = Column(DateTime())
    caldef_dateModified = Column(DateTime())
    caldef_title = Column(String(50))
    caldef_post_id = Column(Integer, ForeignKey('post_data.id'))
    caldef_notes = Column(String(500))
    caldef_projInBp = Column(Boolean)
    caldef_bpInProj = Column(Boolean)
    caldef_bpInProj_cat = Column(String(50))
    caldef_bpInProj_color = Column(String(20))
    caldef_listInProj = Column(Boolean)
    caldef_listInProj_list = Column(Integer, ForeignKey('list_name.id'))
    caldef_listInProj_color = Column(String(20))

    caldef_post = relationship("PostData", foreign_keys=caldef_post_id, backref='post_caldefs')

    def __init__(self, caldef_title, caldef_post):
        self.caldef_title = caldef_title
        self.caldef_post_id = caldef_post

    def __repr__(self):
        return "<CalendarDef('%s - %s')>" % (self.caldef_title, self.caldef_post)

class CalRecord(Base):
    __tablename__ = 'cal_record'

    id = Column(Integer, primary_key=True)
    calrec_dateCreated = Column(DateTime())
    calrec_dateModified = Column(DateTime())
    calrec_title = Column(String(50))
    calrec_startDate = Column(DateTime())
    calrec_endDate = Column(DateTime())
    calrec_doneDate = Column(DateTime())
    calrec_calDef_id = Column(Integer, ForeignKey('calendar_def.id'))
    calrec_notes = Column(String(500))
    calrec_color = Column(String(50))
    calrec_overlap = Column(Boolean)
    calrec_rendering = Column(String(50))
    calrec_groupId = Column(String(50))
    calrec_constraint = Column(String(50))
    calrec_url = Column(String(50))

    calrec_calDef = relationship("CalendarDef", foreign_keys=calrec_calDef_id, backref='caldef_calrecs')

    def __init__(self, calrec_title, calrec_calDef_id, calrec_startDate):
        self.calrec_title = calrec_title
        self.calrec_calDef_id = calrec_calDef_id
        self.calrec_startDate = calrec_startDate

    def __repr__(self):
        return "<CalRecord('%s - %s')>" % (self.calrec_title, self.calrec_startDate)


class Checklist(Base):
    __tablename__ = 'checklist'

    id = Column(Integer, primary_key=True)
    chklst_dateCreated = Column(DateTime())
    chklst_dateModified = Column(DateTime())
    chklst_priority = Column(Integer)
    chklst_done = Column(Boolean)
    chklst_doneDate = Column(DateTime())
    chklst_notes = Column(String(500))

    chklst_masterTarget = relationship("BPRecord", foreign_keys=bprec_masterTarget_id, remote_side=[id])


    def __init__(self, chklst_dateCreated, chklst_Item_title, chklst_category):
        self.chklst_dateCreated = chklst_dateCreated
        self.chklst_Item_title = chklst_Item_title
        self.chklst_category = chklst_category

    def __repr__(self):
        return "<Checklist('%s - %s')>" % (self.chklst_Item_title, self.chklst_doneDate)


class ChklstItem(Base):
    __tablename__ = 'chklst_item'

    id = Column(Integer, primary_key=True)
    chklst_checklist_id = Column(Integer, ForeignKey('checklist.id'))
    chklst_itemDef_id = Column(Integer, ForeignKey('chklst_item.id'))
    chklst_dateCreated = Column(DateTime())
    chklst_dateModified = Column(DateTime())
    chklst_conditional = Column(Boolean)
    chklst_done = Column(Boolean)
    chklst_doneDate = Column(DateTime())
    chklst_notes = Column(String(500))

    chklst_itemDef = relationship("ChklstItemDef", foreign_keys=chklst_itemDef_id, remote_side=[id])
    chklst_checklist = relationship("Checklist", foreign_keys=chklst_checklist_id,)


    def __init__(self, chklst_dateCreated, chklst_Item_title, chklst_category):
        self.chklst_dateCreated = chklst_dateCreated
        self.chklst_Item_title = chklst_Item_title

    def __repr__(self):
        return "<ChklstItem('%s - %s')>" % (self.chklst_Item_title, self.chklst_doneDate)


class printOptsTempl(Base):
    __tablename__ = 'print_opts_templ'

    id = Column(Integer, primary_key=True)
    print_templ_class_id = Column(String(30))
    print_templ_post_id = Column(Integer, ForeignKey('post_data.id'))
    print_templ_user_id = Column(Integer, ForeignKey('users.id'))
    print_templ_userGroup_id = Column(Integer, ForeignKey('user_group.id'))
    print_templ_name = Column(String(30))

    def __init__(self, print_templ_class_id, print_templ_post_id, print_templ_name):
        self.print_templ_class_id = print_templ_class_id
        self.print_templ_post_id = print_templ_post_id
        self.print_templ_name = print_templ_name

class printOptsData(Base):
    __tablename__ = 'print_opts_data'

    id = Column(Integer, primary_key=True)
    print_data_class_id = Column(String(30))
    print_data_def_id = Column(String(30))
    print_data_templ_id = Column(Integer, ForeignKey('print_opts_templ.id'))

    print_data = Column(PickleType())

    print_data_templ = relationship("printOptsTempl", foreign_keys=print_data_templ_id, backref='print_templ_data')

    def __init__(self, print_data_class_id, print_data_def_id, print_data):
        self.print_data_class_id = print_data_class_id
        self.print_data_def_id = print_data_def_id
        self.print_data = print_data

class printTempl(Base):
    __tablename__ = 'print_templ'

    id = Column(Integer, primary_key=True)
    print_user = Column(Integer, ForeignKey('users.id'))
    print_group = Column(Integer, ForeignKey('user_group.id'))
    print_title = Column(String(30))
    print_tab = Column(Integer)
    print_data = Column(JSON)


    def __init__(self, print_title, print_tab):
        self.print_title = print_title
        self.print_tab = print_tab

    def __repr__(self):
        return "<printTempl('%s - %s')>" % (self.print_title, self.print_tab)
    
class ReportPage(Base):
    __tablename__ = 'report_page'

    id = Column(Integer, primary_key=True)
    page_hight = Column(Float) # Page hight
    page_lenth = Column(Float) # Page Lenth
    page_name = Column(String(50)) # Page Name (letter, leagal, tabloid)
    page_title = Column(String(50)) # name of templete
    page_discription = Column(String(200)) # discription of templete
    page_data = Column(PickleType) # The page data
    #page_pages = Column(Integer) # the number of pages
    #page_user =


    def __init__(self, page_lenth, page_hight, page_title):
        self.page_hight = page_hight
        self.page_lenth = page_lenth
        self.page_title = page_title

    def __repr__(self):
        return "<ReportPage('%s')>" % (self.page_title)
    

class Translations(Base):
    __tablename__ = 'translations'

    id = Column(Integer, primary_key=True)
    text = Column(String(500))
    language = Column(String(20))
    translation = Column(String(500))
    translator = Column(String(20))

    def __init__(self, language, text, translation, translator):
        self.language = language
        self.text = text
        self.translation = translation
        self.translator = translator


class buildbaseDB():
    def __init__(self):

        self.file = 'buildbase.db'
        try:
            shutil.copy2('buildbase.bk', os.getenv('USERPROFILE')+"\\buildbase.bk2")
        except:
            pass
        try:
            shutil.copy2('buildbase.db', os.getenv('USERPROFILE')+"\\buildbase.bk")
        except:
            pass
        try:
            shutil.copy2('buildbase.bk', 'buildbase.bk2')
        except:
            pass
        try:
            shutil.copy2('buildbase.db', 'buildbase.bk')
        except:
            pass
        self.server = 'sqlite:///buildbase.db'
        self.SQL_create_class()
        def backup():
            print('Performing Backup...')
            try:
                print('backup - '+'buildbase_'+datetime.datetime.now().strftime('%Y%m%d')+'.bk')
                shutil.copy2('buildbase.db', 'backup\\buildbase_'+datetime.datetime.now().strftime('%Y%m%d')+'.bk')
            except:
                pass
            try:
                print('Clearing Old Backups')
                for root, dirs, files in os.walk('backup', topdown=False):
                    for name in files:
                        file_info = os.stat(os.path.join(root, name))
                        cdate = datetime.date.fromtimestamp(file_info.st_ctime)
                        today = datetime.date.today()
                        if cdate < (today-datetime.timedelta(weeks=2)):
                            os.remove(os.path.join(root, name))
            except:
                pass
            try:
                print('Clearing Session Cache')
                for root, dirs, files in os.walk('sessions', topdown=False):
                    for name in files:
                        file_info = os.stat(os.path.join(root, name))
                        cdate = datetime.date.fromtimestamp(file_info.st_ctime)
                        today = datetime.date.today()
                        if cdate < (today-datetime.timedelta(days=3)):
                            os.remove(os.path.join(root, name))
            except:
                pass
            bkup_timer = threading.Timer(3600.0, backup)
            bkup_timer.start()

        bkup_timer = threading.Timer(60.0, backup)
        #bkup_timer.start()

    def SQL_create_class(self):
        engine = create_engine(self.server)
        session = Session(engine)
        Base.metadata.create_all(engine)
        # column = Column('statrec_data', PickleType())
        # self.add_column(engine, 'stat_record', column)
        session.close()

    def importFile(self, file):
        tmpFile = open(file,'r').read().split('\t\n')
        session = self.getSession()
        for i in tmpFile:
            t_rec = i.split('\t')
            date_time = datetime.datetime.strptime(t_rec[1], '%m/%d/%Y %H:%M:%S')
            rec = Incident(None, date_time, t_rec[3])
            rec.incident_photo = 0
            # rec.incident_saved_date = datetime.datetime.now()
            # rec.incident_edit_date = datetime.datetime.now()
            # rec.incident_saved_user = self.user.id
            # rec.incident_edit_user = self.user.id
            # rec.incident_cat = [session.query(Category).get(int(i)) for i in jason_data['log_cat']]
            session.add(rec)
            session.commit()
        session.close()
    
    def importFile1(self, file):
        tmpFile = open(file,'r').read().split('\n')
        session = self.getSession()
        users = session.query(User).order_by(User.user_username).all()
        categories = session.query(Category).filter(Category.cat_type_id == 1).order_by(Category.cat_title).all()
        orgs = session.query(Org).filter(Org.org_type == 1).order_by(Org.org_name).all()
        date_time = datetime.datetime.now()
        hours = datetime.timedelta(hours=5)
        for i in tmpFile:
            if i.strip():
                date_time = date_time-hours
                rec = Incident(random.choice(users).id , date_time, i)
                rec.incident_photo = 0
                # rec.incident_saved_date = datetime.datetime.now()
                # rec.incident_edit_date = datetime.datetime.now()
                # rec.incident_saved_user = self.user.id
                # rec.incident_edit_user = self.user.id
                rec.incident_cat = [random.choice(categories)]
                rec.incident_org = [random.choice(orgs)]
                session.add(rec)
                print(i)
        session.commit()
        session.close()

    def exportToFile(self):
        file = ''
        for i in self.getWeeks():
            file = file + i.strftime('%d %b %Y')+'\t'+str(self.getWeekPoints(i))+'\n'
        tempFile = open('Stat Data.txt','w')
        tempFile.write(file)
        tempFile.close()

    def recDel(self, ID):
        session = self.getSession()
        to_del = session.query(StatRecord).get(ID)
        session.delete(to_del)
        session.commit()
        session.close()

    def getSession(self):
        engine = create_engine(self.server)
        session = Session(engine)
        return session



if __name__ == '__main__':
    basics_class = basicsClass()
    #basics_class.add_column_foreign('category', 'cat_parent_id', 'category')
    #basics_class.add_column_foreign('category', 'cat_type_id', 'db_type')
    #basics_class.importFile('import.txt')
    basics_class.importFile1('ME1.txt')

    #basics_class.convertToSQLite()
    pass