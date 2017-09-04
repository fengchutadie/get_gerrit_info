#!/usr/bin/python

import sys
import csv
import time

total_map={}
month_map={}
preMonth_map={}
team_map={"Su Xiaolong":0,"Chen Lianbing":0,"Xu Wenjun":0,"Yuan Willy":0,"Hu Bing":0,
			"Xiang Jian":0,"Shi Pucheng":0,"Fang Lei":0,"Ma Cong":0,"Liao leo":0}
member_id=['suxiao','lianbche','wenjuxu','wiyuan','binhu','jiaxiang','pushi','l1fang','congma','leoliao']
Month = {'1':'January', '2':'January', '3':'March', '4':'April', '5':'May', '6':'June', '7':'July', 
			'8':'August', '9':'September', '10':'October', '11':'November', '12':'December'}
review_list=[]

def scan_comments(file_name):
	file = open(file_name,'r')
	reader = csv.reader(file)
	LineNum=1
	cur_len = len(cur_month)
	pre_len = len(pre_month)
	for line in reader:
		if LineNum == 1:
			LineNum = LineNum+1
			continue
		if total_map.has_key(line[2]):
			total_map[line[2]] = total_map[line[2]] + 1
		else:
			total_map[line[2]] = 1
			
		'''if team_map.has_key(line[2]):
			team_map[line[2]] = team_map[line[2]] + 1'''
			
		if line[1][:cur_len] == cur_month:
			if month_map.has_key(line[2]):
				month_map[line[2]] = month_map[line[2]] + 1
			else:
				month_map[line[2]] = 1
		
		if line[1][:pre_len] == pre_month:			
			if team_map.has_key(line[2]):
				team_map[line[2]] = team_map[line[2]] + 1
			'''if preMonth_map.has_key(line[2]):
				preMonth_map[line[2]] = preMonth_map[line[2]] + 1
			else:
				preMonth_map[line[2]] = 1'''
		LineNum = LineNum+1
	file.close()

def scan_review(file_name):	
	file = open(file_name,'r')
	reader = csv.reader(file)
	LineNum=1
	cur_len = len(cur_month)

	for line in reader:
		if LineNum == 1:
			LineNum = LineNum+1
			continue
		
		if line[1] in member_id and line[8][:cur_len] == cur_month: #'2017-08'
			review_list.append(line)
	file.close()	
	
def get_pre_month():
	month = time.localtime()[1]-1 or 12
	year  = time.localtime()[0]
	if month == 12:
		year = year - 1
	if len(str(month)) == 1:
		month = '0' + str(month)
	return str(year) + '-' + str(month)
	
def get_cur_month():
	month = ''
	if len(str(time.localtime()[1])) == 1:
		month = str(time.localtime()[0]) + '-0' + str(time.localtime()[1])
	else:
		month = str(time.localtime()[0]) + '-' + str(time.localtime()[1])
	return month	
	
def print_review_list(list):
	if len(list) == 0:
		print "!!! no record !!!"
	else:
		print "%-8s %-15s %-41s %-10s %-10s %-10s %-10s %-15s %-8s %-s" % \
		('reviewId',  'Author', 'change_id', 'insections', 'deletions', 'create', 'submit', 'approved', 'comments', 'subjuct')
		for line in list:
			print "%-8s %-15s %-41s %-10s %-10s %-10s %-10s %-15s %-8s %-s" % \
			(line[0],line[2],line[3],line[5],line[6],line[7][:10],line[8][:10],line[10],line[11],line[4])

def print_comment_list(map, num=0):
	items=map.items()
	backitems=[[v[1],v[0]] for v in items]
	backitems.sort(reverse=True)		
	if len(backitems) == 0 :
		print "!!! no record !!!"
	else:
		rn = num
		if rn == 0:
			rn = len(backitems)
		else:
			if rn > len(backitems):
				rn = len(backitems)			
				print 'less than 10 members'
		for i in range(0, rn):
			print "%-17s : %3d" %(backitems[i][1] , backitems[i][0])
			
	print ''

def make_statistic():
	scan_comments('comments_Tdd.csv')
	scan_comments('comments_Fdd.csv')	
	print "---- %9s : MACPS comments number Top 10 ----" % time.localtime()[0]
	print_comment_list(total_map, 10)
	print "---- %9s : MACPS comments number Top 10 ----" % Month[str(time.localtime()[1])]
	print_comment_list(month_map, 10)
	print "---- %9s : ACE comments number -------------" % Month[str(time.localtime()[1]-1 or 12)]
	print_comment_list(team_map)
	
	scan_review('review_info_Tdd.csv')
	scan_review('review_info_Fdd.csv')
	print "---- %9s : ACE review info -----------------" % Month[str(time.localtime()[1])]
	print_review_list(review_list)
	
cur_month = get_cur_month()
pre_month = get_pre_month()

if __name__=='__main__':
    make_statistic()
