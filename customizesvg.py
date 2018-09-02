import os
from svgpathtools import svg2paths
from bs4 import BeautifulSoup as bs
import sys
import cairosvg

source = "Social_Media_Assets/original_templates/"
destination = "Social_Media_Assets/generated_templates/"

def paths_to_svgs():
    files = [os.path.join(source, file) for file in os.listdir(source)]
    return files

def replace_city(city="Test City Name"):
    for file in paths_to_svgs():
        final_soup = ""
        #open svg file and navigate XML-tree
        with open(file) as inputxml:
            data = inputxml.read()
            soup = bs(data, 'xml')
            text_blocks = soup.find_all("text")
            for block in text_blocks:
                city_span = block.find("tspan")
                if city_span and len(city_span) > 0:
                    try:
                        city_span.string = city #change name in SVG to city name
                        if city_span.string == city:
                            print(f"City name changed to {city}!")
                    except Exception as ee:
                        print(ee)
            final_soup = soup.prettify
            #save updated file to disk
            save_name = file.split("/")[-1]
            just_name = save_name.split(".")[0]
            with open(f"{destination}svg/{just_name}.svg", "w") as savefile:
                try:
                    savefile.write(str(soup)) #save SVG file to SVG folder
                except Exception as ee2:
                    print(ee2)
            cairosvg.svg2png(url=f"{destination}svg/{just_name}.svg", write_to=f"{destination}png/{just_name}.png")



if __name__ == "__main__":
    new_city =  sys.argv[1]
    if new_city:
        replace_city(new_city)
    else:
        print("Pass 'city name' as an argument.")