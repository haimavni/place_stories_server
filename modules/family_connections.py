from injections import inject
from members_support import get_member_rec
from gluon.storage import Storage
from my_cache import Cache

def get_parents(member_id):
    member_rec = get_member_rec(member_id)
    pa = member_rec.father_id
    ma = member_rec.mother_id
    pa_rec = get_member_rec(pa, prepend_path=True)
    ma_rec = get_member_rec(ma, prepend_path=True)
    parents = Storage()
    if pa_rec:
        parents.pa = pa_rec
    if ma_rec:
        parents.ma = ma_rec
    return parents

def get_parent_list(member_id):
    parents = get_parents(member_id)
    result = []
    for p in parents:
        result.append(parents[p])
    return result

def get_siblings(member_id):
    parents = get_parents(member_id)
    if not parents:
        return []
    db, VIS_NEVER = inject('db', 'VIS_NEVER')
    pa, ma = parents.pa, parents.ma
    q = (db.TblMembers.id != member_id) & (db.TblMembers.visibility != VIS_NEVER) & (db.TblMembers.deleted == False)
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
    if not hidden_too:
        q &= (db.TblMembers.visibility != VIS_NEVER)
    q &= (db.TblMembers.deleted == False)
    lst = db(q).select(db.TblMembers.id, db.TblMembers.date_of_birth, orderby=db.TblMembers.date_of_birth)
    lst = [get_member_rec(rec.id, prepend_path=True) for rec in lst]
    return lst

def get_spouses(member_id):
    children = get_children(member_id, hidden_too=True)
    member_rec = get_member_rec(member_id)
    spouses1 = [child.father_id for child in children if child.father_id and child.father_id != member_id and not child.divorced_parents]
    spouses2 = [child.mother_id for child in children if child.mother_id and child.mother_id != member_id and not child.divorced_parents]
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
    result = [member for member in result if member]
    return result 

def get_family_connections(member_id):
    auth, VIS_NEVER = inject('auth', 'VIS_NEVER')
    ###debugging only! get_all_relatives(member_id)
    #fc = get_all_family_connections(member_id)
    #path = fc.find_path(493)
    
    parents = get_parents(member_id)
    for p in ['pa', 'ma']:
        if parents[p] and parents[p].visibility == VIS_NEVER:
            parents[p] = None
    privileges = auth.get_privileges()
    is_admin = privileges.ADMIN if privileges else False
    result = Storage(
        parents=parents,
        siblings=get_siblings(member_id),
        spouses=get_spouses(member_id),
        children=get_children(member_id, hidden_too=is_admin)
    )
    result.hasFamilyConnections = len(result.parents) > 0 or len(result.siblings) > 0 or len(result.spouses) > 0 or len(result.children) > 0
    return result

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
        
    