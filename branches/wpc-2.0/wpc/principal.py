import win32security
import ntsecuritycon
import _winreg
import win32service
import win32con
import wpc.conf

# These have sids, perhaps a domain
class principal:
	def __init__(self, sid):
		self.name = None
		self.domain = None
		self.set_sid(sid)
		self.type = None
		self.sid_string = None
		self.trusted = None
		self.trusted_set = 0
		self.cant_resolve = 0
		
	def set_sid(self, sid):
		self.sid = sid
	
	def get_remote_server(self):
		return wpc.conf.remote_server
		
	def get_sid(self):
		return self.sid
			
	def get_sid_string(self):
		if self.sid_string == None:
			self.sid_string = win32security.ConvertSidToStringSid(self.get_sid())
		return self.sid_string
	
	def get_fq_name(self):
		if self.cant_resolve:
			return self.get_sid_string()
		else:
			return self.get_domain() + "\\" + self.get_name()
		
	def get_type(self):
		if self.type == None:
			self.get_name() # side effect sets type
		return self.type
	
#	def get_principal(self):
		#if self.__class__.__name__ == "principal":
			#return self
		#else:
			#return self.principal
		
	def get_domain(self):
		if self.domain == None:
			self.get_name() # side effect sets domain
		return self.domain
	
	def set_type(self, type):
		self.type = type
	
	def get_type_string(self):
		return self.resolve_type(self.get_type())
	
	def resolve_type(self, type):
		return wpc.conf.sid_type[type]
	
	def is_group_type(self):
		return wpc.conf.sid_is_group_type[self.get_type()]
	
	def set_domain(self, domain):
		self.domain = domain

	def get_name(self):
		if self.name == None or self.get_type() == None:
			sid = self.get_sid()
			if sid == None:
				self.set_type('N/A')
				self.set_domain('[none]')
				self.name = '[none]'
			else:
				try:
					#print wpc.conf.cache.LookupAccountSid(self.get_remote_server(), self.get_sid())
					self.name, domain, type = list(wpc.conf.cache.LookupAccountSid(self.get_remote_server(), self.get_sid()))
				except:
					self.cant_resolve = 1
					self.name, domain, type = self.get_sid_string(), "[unknown]", 8
				self.set_type(type)
				self.set_domain(domain)
		return self.name
	
#	def is_trusted(self):
#		for p in wpc.conf.trusted_principals:
#			if self.get_sid() == p.get_sid():
#				return 1
#		return 0
	
	def is_trusted(self):
		#print "Testing if %s is trusted" % self.get_fq_name()
		if self.trusted_set:
			#print "Cache result returned for trust of %s: %s" % (self.get_fq_name(), self.trusted)
			return self.trusted
# TODO			
#		if self.is_group_type():
#			g = group(self.get_sid())
#			print "Group type"
#			# Groups with zero members are trusted - i.e. not interesting
#			if len(g.get_members()) == 0:
#				self.trusted_set = 1
#				self.trusted = 1
#				print "%s is trusted.  Group with no members" % self.get_fq_name()
#				return 1
				
		for p in wpc.conf.trusted_principals:
			# This also recurses through sub groups
			#print "Testing if %s is in %s" % (self.get_fq_name(), p.get_fq_name())
			if self.is_in_group(p):
				#print "Yes"
				self.trusted_set = 1
				self.trusted = 1
				#print "%s is trusted.  Member of trusted group %s" % (self.get_fq_name(), p.get_fq_name())
				return 1
			else:
				#print "No"
#				print "User type"
				if p.get_sid() == self.get_sid():
					self.trusted_set = 1
					self.trusted = 1
					#print "%s is trusted.  Is trusted user %s" % (self.get_fq_name(), p.get_fq_name())
					return 1
		self.trusted_set = 1
		self.trusted = 0		
		#print "%s is not trusted" % self.get_fq_name()
		return 0
		
	def is_in_group(self, group):
		#print "is_in_group called for %s, %s" % (self.get_fq_name(), group.get_name())
		return wpc.conf.cache.is_in_group(self, group)
			
