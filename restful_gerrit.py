#!/usr/bin/python
import os
import json
import pycurl
import StringIO
import re
import csv
import datetime
import time
import sys

class Gerrit_info:

	reviewTitle=("reviewId","author_id","author","change_id","subject","insertion","deletions","created","submit","approve_id","approved","comment_num")
	commentTitle=("reviewId","date","Comments contributor","comments")		
		
	def get_json(self, url):
		#print url
		c = pycurl.Curl()
		output = StringIO.StringIO()
		c.setopt(pycurl.URL, url)
		c.setopt(pycurl.USERPWD, self.user_pwd)
		c.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_1_0)
		c.setopt(pycurl.HTTPAUTH,pycurl.HTTPAUTH_DIGEST)
		c.setopt(pycurl.SSL_VERIFYPEER, False)
		c.setopt(pycurl.WRITEFUNCTION, output.write)
		
		info_list = {}
		try_num = 3
		while try_num > 0:
			try:
				c.perform()
				info_list = json.loads(output.getvalue().replace(")]}'",""))
				try_num = -1
			except ValueError as e:
				try_num -= 1
				time.sleep(5)
			finally:
				if try_num == 0:
					print "ValueError : " + url
					
		output.close()
		c.close()
		return info_list
		
	'''
	it will taks about 5s to get 500 items from gerrit, 
	suppose at most there are (overlap =) 5 new times added in DB in the interval
	'''
	def get_merge_list(self, cmdstr, status='open'):
		num = 0
		overlap = 5
		tail_list = []
		while True:
			moreChange = False
			
			if len(self.commit_info) > overlap:
				tail_list = self.commit_info[-overlap:]
			else:
				tail_list = []
			
			cmd = cmdstr %  (num,status)
			print cmd
			if os.system(cmd) != 0:
				print "cmd fail status:%s , num:%d" %(status, num)
				break
			print "cmd success status:%s , num:%d" %(status, num)

			file = open("tmp")
			for line in file:
				merge = json.loads(line[:-1])
				if merge.has_key('moreChanges'):
					if str(merge["moreChanges"]) == 'True':
						num += 500
						moreChange = True
					break
					
				if str(merge["id"]) not in tail_list:
					self.commit_info.append(str(merge["id"]))

			file.close()
			if moreChange == False:
				if status == 'open':
					status = 'merge'
					num = 0
				else:
					break
			#increase 5 overlap per gerrit query
			overlap += 5
		
	def get_reviewInfo(self, host, port, project, branch, status='merge', interval=''):
		print "get merge list"
		cmd = 'ssh -p %d %s gerrit query --format=JSON --start %%d status:%%s limit:500 project:%s branch:%s %s > tmp' % (port,host,project,branch,interval)
		self.get_merge_list(cmd, status)
		for info in self.commit_info:
			if info in self.protect_list:
				break
			self.get_commit_info(info,interval)
		
		self.Exit()
		
	def get_protected_list(self, file_name):
		filetoread=open(file_name,'r')
		reader=csv.reader(filetoread)
		num = 0
		for line in reader:
			if  num == 50:
				break
			num += 1
			self.protect_list.append(line[3])
		filetoread.close()

	def extend_review(self, new_review, old_review, new_comment, old_comment):
		reviewfile_r = open(old_review, 'rb')
		rev_reader=csv.reader(reviewfile_r)
		reviewfile_a = open(new_review, 'ab')
		rev_writer=csv.writer(reviewfile_a)
		
		commentfile_r = open(old_comment, 'rb')
		comment_reader=csv.reader(commentfile_r)
		commentfile_a = open(new_comment, 'ab')
		comment_writer=csv.writer(commentfile_a)
		
		skip_line = True
		for line in rev_reader:
			if skip_line == True:
				skip_line = False
				continue
			rev_writer.writerow(line)
		skip_line = True
		for line in comment_reader:
			if skip_line == True:
				skip_line = False
				continue
			comment_writer.writerow(line)

		reviewfile_r.close()
		reviewfile_a.close()
		commentfile_r.close()
		commentfile_a.close()
		
	#get yesterday date	
	def get_interval(self):
		return 'after:'+ str(datetime.date(time.localtime()[0],time.localtime()[1],time.localtime()[2])+datetime.timedelta(days=-1))
	
class Hz_gerrit(Gerrit_info):
	host = 'hztddgit.china.nsn-net.net'
	port = 29418
	branch = 'fddps~trunk~'
	gerrit_url = "http://hztddgit.china.nsn-net.net/gerrit/"
	user_pwd = "congma:wDd73gMo0+r+Et/QNInrYtiMSz0TWP3UnBbPCm/lOg"
	commit_info=[]
	protect_list = []
	def __init__(self):
		self.get_protected_list('review_info_Tdd.csv')
		self.review_csvfile = file('review_info_Tdd.csv', 'ab')
		self.review_writer = csv.writer(self.review_csvfile)
		#self.review_writer.writerow(self.reviewTitle)
		
		self.comment_csvfile = file('comments_Tdd.csv', 'ab')
		self.comment_writer = csv.writer(self.comment_csvfile)
		#self.comment_writer.writerow(self.commentTitle)

		self.new_review = file('review_Tdd_tmp.csv', 'wb')
		self.new_review_writer = csv.writer(self.new_review)
		self.new_review_writer.writerow(self.reviewTitle)
		
		self.new_comment = file('comments_Tdd_tmp.csv', 'wb')
		self.new_comment_writer = csv.writer(self.new_comment)
		self.new_comment_writer.writerow(self.commentTitle)
		
	def Exit(self):
		self.review_csvfile.close()
		self.comment_csvfile.close()
		self.new_review.close()
		self.new_comment.close()

	def get_comments(self, review_url, patch_num, reviewId, date, author, interval):
		n = 1
		total_comments = 0
		dupComment = []

		while n <= patch_num:
			url = review_url+'/revisions/'+str(n)+'/comments'
			comments = self.get_json(url)
			for comment in comments:
				for item in comments[comment]:
					if str(item["author"]["name"]) == author:#delete author's comment
						continue
					if str(item["message"]).lower() == 'done'.lower():#delete "done" comment
						continue
					if re.sub('[^a-zA-Z0-9]','',str(item["message"])) in dupComment:#delete duplicated comment
						continue
					dupComment.append(re.sub('[^a-zA-Z0-9]','',str(item["message"])))
					comment_list=[]
					comment_list.append(reviewId)
					comment_list.append(date)
					comment_list.append(item["author"]["name"])
					comment_list.append(str(item["message"]))
					if interval == '':
						self.comment_writer.writerow(comment_list)
					else:
						self.new_comment_writer.writerow(comment_list)
					total_comments = total_comments + 1
			n = n+1
		return total_comments

	def get_commit_info(self, commit_id, interval):
		print commit_id
		#review_url =self.gerrit_url+'a/changes/'+commit_id
		review_url =self.gerrit_url+'a/changes/'+self.branch+commit_id
		review_result=[]
		review_info = self.get_json(review_url+'/detail')
		if len(review_info) == 0:
			print commit_id + " can't get JSON"
			return
		review_result.append(review_info["_number"])
		review_result.append(review_info["owner"]["username"])
		review_result.append(review_info["owner"]["name"])
		review_result.append(review_info["change_id"])
		review_result.append(review_info["subject"])
		review_result.append(review_info["insertions"])
		review_result.append(review_info["deletions"])
		review_result.append(review_info["created"][:19])
		
		findApprove=False
		for msg in review_info["messages"]:
			if "Code-Review+2" in msg["message"]:
				review_result.append(msg["date"][:19])
				findApprove=True
				break	
		if findApprove == False:
			review_result.append(review_info["updated"][:19])

		review_result.append(review_info["labels"]["Code-Review"]["approved"]["username"])
		review_result.append(review_info["labels"]["Code-Review"]["approved"]["name"])

		patch_num = review_info["messages"][len(review_info["messages"])-1]["_revision_number"]
		num = self.get_comments(review_url,patch_num,review_info["_number"],review_info["updated"][:19],review_info["owner"]["name"],interval)
		review_result.append(str(num))
		
		if interval == '':
			self.review_writer.writerow(review_result)
		else:
			self.new_review_writer.writerow(review_result)
			
	def get_all_review(self):
		self.get_reviewInfo(self.host, self.port, 'fddps', 'trunk')
		
	def get_new_review(self):
		self.get_reviewInfo(self.host, self.port, 'fddps', 'trunk', interval=self.get_interval())
		self.extend_review('review_Tdd_tmp.csv', 'review_info_Tdd.csv', 'comments_Tdd_tmp.csv', 'comments_Tdd.csv')
	

class Fdd_gerrit(Gerrit_info):
	host = 'ullteb150.emea.nsn-net.net'
	port = 29422
	branch = 'BTS_SC_MAC_PS_WMP5~trunk~'
	gerrit_url = "https://ullteb150.emea.nsn-net.net:8092/"
	user_pwd = "congma:O2+PY7awJ8s7XyMNj52R+7B7ZoYbpG+HUsDiUU0JwQ"
	commit_info = []
	name_list = {}
	protect_list = []
	def __init__(self):
		self.get_protected_list('review_info_Fdd.csv')
		self.get_namelist()
		self.review_csvfile = file('review_info_Fdd.csv', 'ab')
		self.review_writer = csv.writer(self.review_csvfile)
		#self.review_writer.writerow(self.reviewTitle)
		
		self.comment_csvfile = file('comments_Fdd.csv', 'ab')
		self.comment_writer = csv.writer(self.comment_csvfile)
		#self.comment_writer.writerow(self.commentTitle)

		self.new_review = file('review_Fdd_tmp.csv', 'wb')
		self.new_review_writer = csv.writer(self.new_review)
		self.new_review_writer.writerow(self.reviewTitle)
		
		self.new_comment = file('comments_Fdd_tmp.csv', 'wb')
		self.new_comment_writer = csv.writer(self.new_comment)
		self.new_comment_writer.writerow(self.commentTitle)

	def Exit(self):
		self.review_csvfile.close()
		self.comment_csvfile.close()
		self.new_review.close()
		self.new_comment.close()

	def get_namelist(self):
		filetoread=open('name_list','r')	
		reader=csv.reader(filetoread)
		for line in reader:
			self.name_list[line[0]]=line[1]
		filetoread.close()
		
	def get_comments(self, review_url, patch_num, reviewId, date, author, interval):
		n = 1
		total_comments = 0
		dupComment = []

		while n <= patch_num:
			url = review_url + '/comments'
			comments = self.get_json(url)
			for comment in comments:
				for item in comments[comment]:
					if str(item["author"]["name"]) == author:#delete author's comment
						continue
					if str(item["message"]).lower() == 'done'.lower():#delete "done" comment
						continue
					if re.sub('[^a-zA-Z0-9]','',str(item["message"])) in dupComment:#delete duplicated comment
						continue
					dupComment.append(re.sub('[^a-zA-Z0-9]','',str(item["message"])))
					comment_list=[]
					comment_list.append(reviewId)
					comment_list.append(date)
					
					if self.name_list.has_key(item["author"]["username"]):
						comment_list.append(self.name_list[item["author"]["username"]])
					else:
						comment_list.append(item["author"]["name"])

					comment_list.append(str(item["message"]))

					if interval == '':
						self.comment_writer.writerow(comment_list)
					else:
						self.new_comment_writer.writerow(comment_list)

					total_comments = total_comments + 1
			n = n+1	
		
		return total_comments

	def get_commit_info(self, commit_id, interval):
		review_url =self.gerrit_url+'a/changes/'+ self.branch + commit_id
		print commit_id
		review_info = self.get_json(review_url+'/detail')
		
		if len(review_info) == 0:
			print commit_id + " can't get JSON"
			return
		if (str(review_info['status']) == 'NEW' and str(review_info['submittable']) == 'False'):
			print commit_id + "  not invalid"
			return
			
		review_result=[]
		review_result.append(review_info["_number"])
		name=''

		if review_info["owner"]["username"] != 'c_lteulm':
			review_result.append(review_info["owner"]["username"])
			if self.name_list.has_key(review_info["owner"]["username"]):
				review_result.append(self.name_list[review_info["owner"]["username"]])
			else:
				review_result.append(review_info["owner"]["name"])
			name = review_info["owner"]["name"]
		else:
			if review_info["subject"] == 'auto ECL-update':
				review_result.append(review_info["owner"]["username"])
				if self.name_list.has_key(review_info["owner"]["username"]):
					review_result.append(self.name_list[review_info["owner"]["username"]])
				else:
					review_result.append(review_info["owner"]["name"])

				name = review_info["owner"]["name"]
			else:
				review_result.append(review_info["labels"]["Code-Review"]["all"][0]["username"])
				
				if self.name_list.has_key(review_info["labels"]["Code-Review"]["all"][0]["username"]):
					review_result.append(self.name_list[review_info["labels"]["Code-Review"]["all"][0]["username"]])
				else:
					review_result.append(review_info["labels"]["Code-Review"]["all"][0]["name"])
				
				name = review_info["labels"]["Code-Review"]["all"][0]["name"]

		review_result.append(review_info["change_id"])
		review_result.append(review_info["subject"])
		review_result.append(review_info["insertions"])
		review_result.append(review_info["deletions"])
		review_result.append(review_info["created"][:19])

		findApprove=False
		for msg in review_info["messages"]:
			if "Code-Review+2" in msg["message"]:
				review_result.append(msg["date"][:19])
				findApprove=True
				break	
		if findApprove == False:
			review_result.append(review_info["updated"][:19])

		review_result.append(review_info["labels"]["Code-Review"]["approved"]["username"])

		if self.name_list.has_key(review_info["labels"]["Code-Review"]["approved"]["username"]):
			review_result.append(self.name_list[review_info["labels"]["Code-Review"]["approved"]["username"]])
		else:
			review_result.append(review_info["labels"]["Code-Review"]["approved"]["name"])

		num = self.get_comments(review_url,1,review_info["_number"],review_info["updated"][:19],name, interval)
		review_result.append(str(num))
		if interval == '':
			self.review_writer.writerow(review_result)
		else:
			self.new_review_writer.writerow(review_result)		
		
	def get_all_review(self):
		self.get_reviewInfo(self.host, self.port, 'BTS_SC_MAC_PS_WMP5', 'trunk', status='open')
		
	def get_new_review(self):
		#self.get_protected_list('review_info_Fdd.csv')
		self.get_reviewInfo(self.host, self.port, 'BTS_SC_MAC_PS_WMP5', 'trunk', status='open', interval=self.get_interval())
		self.extend_review('review_Fdd_tmp.csv', 'review_info_Fdd.csv', 'comments_Fdd_tmp.csv', 'comments_Fdd.csv')
		
def get_gerrit_info():
	#avoid to parse non ASCII code
	reload(sys) 
	sys.setdefaultencoding('utf8')
	
	hz = Hz_gerrit()
	hz.get_new_review()
	#hz.get_all_review()

	time.sleep(10)
	fdd = Fdd_gerrit()
	fdd.get_new_review()
	#fdd.get_all_review()

	
if __name__=='__main__':
	get_gerrit_info()
	#make_statistic()