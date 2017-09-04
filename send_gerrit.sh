#!/bin/bash
cd ~/auto_script/get_gerrit_info
DATE=$(date +%Y-%m-%d)

./restful_gerrit.py > log/result_$DATE 2>&1

if [ -f "comments_Fdd.csv " ]; then
	mv comments_Fdd.csv history/comments_Fdd_$DATE.csv
else
	echo " no comments_Fdd.csv" >> log/result_$DATE
fi
if [ -f "comments_Fdd_tmp.csv" ]; then
	mv comments_Fdd_tmp.csv comments_Fdd.csv
else
	echo " no comments_Fdd_tmp.csv" >> log/result_$DATE
fi

if [ -f "review_info_Fdd.csv" ]; then
	mv review_info_Fdd.csv history/review_info_Fdd_$DATE.csv
else
	echo " no review_info_Fdd.csv" >> log/result_$DATE
fi
if [ -f "review_Fdd_tmp.csv" ]; then
	mv review_Fdd_tmp.csv review_info_Fdd.csv
else
	echo " no review_Fdd_tmp.csv" >> log/result_$DATE
fi

if [ -f "review_info_Tdd.csv" ]; then
	mv review_info_Tdd.csv history/review_info_Tdd_$DATE.csv
else
	echo " no review_info_Tdd.csv" >> log/result_$DATE
fi
if [ -f "review_Tdd_tmp.csv" ]; then
	mv review_Tdd_tmp.csv review_info_Tdd.csv
else
	echo " no review_Tdd_tmp.csv" >> log/result_$DATE
fi
if [ -f "comments_Tdd.csv " ]; then
	mv comments_Tdd.csv history/comments_Tdd_$DATE.csv
else
	echo " no comments_Tdd.csv" >> log/result_$DATE
fi
if [ -f "comments_Tdd_tmp.csv" ]; then
	mv comments_Tdd_tmp.csv comments_Tdd.csv
else
	echo " no comments_Tdd_tmp.csv" >> log/result_$DATE
fi

./make_statistic.py > log/mail_text

mailx -s "MacPs code review info($DATE)"  -r "cong.2.ma@nokia.com (Ma Cong)"  I_MN_P_LTE_RD_DEVHZ2_FT2@internal.nsn.com < log/mail_text  
echo "MacPs code RAW review info($DATE)" |mail -s "MacPs code RAW review info($DATE)" -a comments_Tdd.csv  -a comments_Fdd.csv -a review_info_Fdd.csv -a review_info_Tdd.csv -r "cong.2.ma@nokia.com (Ma Cong)" cong.2.ma@nokia.com jinyong.yang@nokia.com

