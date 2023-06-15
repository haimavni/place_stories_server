from .injections import inject
from .members_support import get_member_rec
from gluon.storage import Storage
from .my_cache import Cache
import datetime
from enum import Enum

def get_parents(member_id):
    member_rec = get_member_rec(member_id)
    pa = ma = pa2 = ma2 = None
    if member_rec.father2_id:
        pa = member_rec.father_id
        pa2 = member_rec.father2_id
    elif member_rec.mother2_id:
        ma = member_rec.mother_id
        ma2 = member_rec.mother2_id
    else:
        pa = member_rec.father_id
        ma = member_rec.mother_id
    parents = Storage()
    if pa:
        pa_rec = get_member_rec(pa, prepend_path=True)
        parents.pa = pa_rec
    if ma:
        ma_rec = get_member_rec(ma, prepend_path=True)
        parents.ma = ma_rec
    if pa2:
        pa2_rec = get_member_rec(pa2, prepend_path=True)
        parents.pa2 = pa2_rec
    if ma2:
        ma2_rec = get_member_rec(ma2, prepend_path=True)
        parents.ma2 = ma2_rec
    pars = parent_list(parents)
    if len(pars) == 2:
        parents.par1, parents.par2 = pars
    elif len(pars) == 1:
        parents.par1 = pars[0]
    
    return parents

def parent_list(parents):
    pars = []
    for p in ['pa', 'ma', 'pa2', 'ma2']:
        if parents[p]:
            pars.append(parents[p])
    return pars

def get_grand_parents(member_id):
    grand_parents = []
    parents = get_parents(member_id)
    found = False
    for who in ['pa', 'ma', 'pa2', 'ma2']:
        parent = parents[who]
        if parent:
            mid = parent.id
            grands = parent_list(get_parents(mid))
            if grands:
                found = True
                grand_parents += grands
    if not found:
        grand_parents = None
    return grand_parents

def get_parent_list(member_id):
    parents = get_parents(member_id)
    result = []
    for p in parents:
        result.append(parents[p])
    return result

def get_siblings(member_id, hidden_too=False):
    parents = get_parents(member_id)
    if not parents:
        return []
    db, VIS_NEVER = inject('db', 'VIS_NEVER')
    pa, ma = parents.pa, parents.ma
    q = (db.TblMembers.id != member_id) & (db.TblMembers.deleted == False)
    if not hidden_too:
        q &= (db.TblMembers.visibility != VIS_NEVER)
    if pa:
        lst1 = db(q & (db.TblMembers.father_id==pa.id)).select(orderby=db.TblMembers.date_of_birth) if pa else []
        lst1 = [r.id for r in lst1]
    else:
        lst1 = []
    if ma:
        lst2 = db(q & (db.TblMembers.mother_id==ma.id)).select(orderby=db.TblMembers.date_of_birth) if ma else []
        lst2 = [r.id for r in lst2]
    else:
        lst2 = []
    lst = list(set(lst1 + lst2)) #make it unique
    lst = [get_member_rec(id, prepend_path=True) for id in lst]
    for rec in lst:
        if not rec.date_of_birth:
            rec.date_of_birth = datetime.date(year=1, month=1, day=1) #should not happen but it did...
    lst = sorted(lst, key=lambda rec:rec.date_of_birth.raw)
    return lst

def get_children(member_id, hidden_too=False):
    member_rec = get_member_rec(member_id)
    db, VIS_NEVER = inject('db', 'VIS_NEVER')
    q = (db.TblMembers.mother_id==member_id) | (db.TblMembers.father_id==member_id)
    q |= (db.TblMembers.mother2_id==member_id) | (db.TblMembers.father2_id==member_id)
    if not hidden_too:
        q &= (db.TblMembers.visibility != VIS_NEVER)
    q &= (db.TblMembers.deleted == False)
    lst = db(q).select(db.TblMembers.id, db.TblMembers.date_of_birth, orderby=db.TblMembers.date_of_birth)
    lst = [get_member_rec(rec.id, prepend_path=True) for rec in lst]
    return lst

def get_spouses(member_id):
    children = get_children(member_id, hidden_too=True)
    member_rec = get_member_rec(member_id)
    if member_rec.father2_id:
        spouses1 = [child.father_id for child in children if child.father_id and child.father_id != member_id and child.parents_marital_status != 2]
        spouses2 = [child.father2_id for child in children if child.father2_id and child.father2_id != member_id and child.parents_marital_status != 2]
    elif member_rec.mother2_id:
        spouses1 = [child.mother_id for child in children if child.mother_id and child.mother_id != member_id and child.parents_marital_status != 2]
        spouses2 = [child.mother2_id for child in children if child.mother2_id and child.mother2_id != member_id and child.parents_marital_status != 2]
    else:
        spouses1 = [child.father_id for child in children if child.father_id and child.father_id != member_id and child.parents_marital_status != 2]
        spouses2 = [child.mother_id for child in children if child.mother_id and child.mother_id != member_id and child.parents_marital_status != 2]
    spouses = spouses1 + spouses2
    spouses = [sp for sp in spouses if sp]  #to handle incomplete data
    visited = set([])
    spouses1 = []
    for sp_id in spouses:
        if sp_id in visited:
            continue
        else:
            visited |= set([sp_id])
            spouses1.append(sp_id)
    spouses = spouses1        
    ###spouses = list(set(spouses))  ## nice but does no preserve order
    result = [get_member_rec(m_id, prepend_path=True) for m_id in spouses]
    result = [spouse for spouse in result if spouse]
    for spouse in result:
        children = get_member_spouse_children(member_id, spouse.id)
        for child in children:
            ms = child.parents_marital_status or 0
            spouse.marital_status = "divorced" if ms == 1 else "togetherxxx"
            break
    return result

def get_family_connections(member_id):
    auth, VIS_NEVER = inject('auth', 'VIS_NEVER')
    ###debugging only! get_all_relatives(member_id)
    #fc = get_all_family_connections(member_id)
    #path = fc.find_path(493)
    
    parents = get_parents(member_id)
    for p in ['pa', 'ma', 'pa2', 'ma2']:
        if parents[p] and parents[p].visibility == VIS_NEVER:
            parents[p] = None
    privileges = auth.get_privileges()
    is_admin = privileges.ADMIN if privileges else False
    result = Storage(
        grand_parents=get_grand_parents(member_id),
        parents=parents,
        siblings=get_siblings(member_id, hidden_too=is_admin),
        spouses=get_spouses(member_id),
        children=get_children(member_id, hidden_too=is_admin)
    )
    result.hasFamilyConnections = len(result.parents) > 0 or len(result.siblings) > 0 or len(result.spouses) > 0 or len(result.children) > 0
    return result

def get_member_spouse_children(member_id, spouse_id):
    db = inject("db")
    member_rec = get_member_rec(member_id)
    spouse_rec = get_member_rec(spouse_id)
    if member_rec.gender == 'M':
        qm = (db.TblMembers.father_id==member_id) | (db.TblMembers.father2_id==member_id)
    else:
        qm = (db.TblMembers.mother_id==member_id) | (db.TblMembers.mother2_id==member_id)
    if spouse_rec.gender == 'M':
        qs = (db.TblMembers.father_id==spouse_id) | (db.TblMembers.father2_id==spouse_id)
    else:
        qs = (db.TblMembers.mother_id==spouse_id) | (db.TblMembers.mother2_id==spouse_id)
    return db(qm & qs).select()

class AllFamilyConnections:
    
    def __init__(self, member_id):
        self.member_id = member_id
        self.visited =  set([member_id])
        self.levels = [set([member_id])]
        self.walk()
        
    def walk(self):
        this_level = set([])
        prev = self.levels[-1]
        for m_id in prev:
            immediates = self.get_all_first_degree_relatives(m_id)
            for i in immediates:
                if i in self.visited:
                    continue
                this_level |= set([i]) 
                self.visited |= set([i])
        if this_level:
            self.levels.append(this_level)
            self.walk()
            
    def get_all_first_degree_relatives(self, member_id):
        result = set([rec.id for rec in get_parent_list(member_id)])
        result |= set([rec.id for rec in get_siblings(member_id)])
        result |= set([rec.id for rec in get_spouses(member_id)])
        result |= set([rec.id for rec in get_children(member_id)])
        return result
    
    def get_all_relatives(self):
        return self.levels
    
    def _find_path(self, other_member_id, origin, level, max_level):
        if level > max_level:
            return None
        fdr = self.get_all_first_degree_relatives(origin)
        for mid in self.levels[level] & fdr:
            if mid==other_member_id:
                return [mid]
        for mid in self.levels[level] & fdr:
            path = self._find_path(other_member_id, mid, level + 1, max_level)
            if path:
                return [mid] + path
        return None
    
    def find_path(self, other_member_id):
        max_level = 1000
        for m, level in enumerate(self.levels):
            if other_member_id in level:
                max_level = m;
                break;
        if max_level > 100:
            return None #should never happen
        return self._find_path(other_member_id, origin=self.member_id, level=1, max_level=max_level)
    
def _get_all_family_connections(member_id):
    return AllFamilyConnections(member_id)

def get_all_family_connections(member_id, refresh=False):
    c = Cache('FAMILY-CONNECTIONS-{}', format(member_id))
    return c(lambda: _get_all_family_connections(member_id), refresh=refresh, time_expire=3600)

class Relation(Enum):
    PARENT=1
    SIBLING=2
    SPOUSE=3
    CHILD=4
        
class BuildFamilyConnections:
    
    def __init__(self):
        self.levels = []

    def build(self, max_count=9999):
        db, comment = inject("db", "comment")
        comment("started build of family connections")
        count = 0
        for member in db((db.TblMembers.deleted != True) & (db.TblMembers.family_connections_stored != True)).select():
            relatives = self.get_all_first_degree_relatives(member.id)
            for relation in sorted(relatives):
                for mem_id in relatives[relation]:
                    db.TblFamilyConnections.insert(member_id=member.id, relative_id=mem_id, relation=relation)
            member.update_record(family_connections_stored=True)
            count += 1
            if count % 100 == 0:
                db.commit()
            if count > max_count:
                break
        comment("finished build of family connections")
        return count
    
    def get_all_first_degree_relatives(self, member_id):
        result = Storage()
        result[Relation.PARENT.value] = set([rec.id for rec in get_parent_list(member_id) if rec])
        result[Relation.SIBLING.value] = set([rec.id for rec in get_siblings(member_id) if rec])
        result[Relation.SPOUSE.value] = set([rec.id for rec in get_spouses(member_id) if rec])
        result[Relation.CHILD.value] = set([rec.id for rec in get_children(member_id) if rec])
        return result
    
    def recalculate_member_connections(self, member_id):
        db(db.TblMembers.id==member_id).update(family_connections_stored = False)
        #todo: which records of TblFamilyConnections to delete?

class CalcFamilyConnections:

    def __init__(self) -> None:
        db = inject("db")
        self.dic = Storage()
        for rec in db(db.TblFamilyConnections).select(orderby=db.TblFamilyConnections.relation):
            if rec.member_id not in self.dic:
                self.dic[rec.member_id] = []
            self.dic[rec.member_id].append(rec.relative_id)

    def calc_levels(self, member_id):
        levels = [[member_id]]
        visited = set([member_id])
        for i in range(100):
            curr_level = levels[-1]
            next_level = []
            for mid in curr_level:
                tmp = self.dic[mid]
                if not tmp:
                    continue
                tmp = [m for m in tmp if m not in visited]
                visited |= set(tmp)
                next_level += tmp
            if not next_level:
                break
            levels.append(next_level)
        return levels
    
    def find_path(self, member_id, other_member_id):
        levels = self.calc_levels(member_id)
        n = None
        for j, level in enumerate(levels):
            if other_member_id in set(level):
                n = j
                break
        if not n:
            return None
        mid = other_member_id
        path = [other_member_id]
        for i in range(n-1, 1, -1):
            lvl = set(levels[i])
            relatives = self.dic[mid]
            relatives = [r for r in relatives if r in lvl]
            mid = relatives[0]
            path.append(mid)
        path.reverse()
        return path

def build_family_connections(max_count=9999):
    fc = BuildFamilyConnections()
    return fc.build(max_count)

def calc_family_connections(member_id):
    cfc = CalcFamilyConnections()
    return cfc.calc_levels(member_id)

def find_family_path(member1, member2):
    cfc = CalcFamilyConnections()
    return cfc.find_path(member1, member2)
