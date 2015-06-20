from bs4 import BeautifulSoup

file_name_list = open('data/file_list', 'r')
output = open('output', 'w')

for line in file_name_list:
	file_name = line.strip('\n')
	file_path = 'data/'
	file_ptr = open(file_path + file_name, 'r')
	msg = file_ptr.read()
	soup = BeautifulSoup(msg)

	timestamp = file_name.split('_')[1]

	for item_string in soup.find_all('div', {"class":"p3_tab_h2"}):
		array = []
		for index in (1,3,5,7,9,11):
			content = unicode(item_string.contents[index].string).strip(' \n')
			array.append(content)
		output.write('%s %s %s %s %s %s %s\n' % (timestamp, array[0].encode('utf-8'),array[1].encode('utf-8'),array[2].encode('utf-8'),array[3].encode('utf-8'),array[4].encode('utf-8'),array[5].encode('utf-8')))

	# print soup.prettify('utf-8')
	

