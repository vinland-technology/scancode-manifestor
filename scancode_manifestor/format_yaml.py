    
class YamlFormatter:

    def __init__(self, args, utils):
        pass

    def format(self, report):
        return "not implemented yet"
    
    def format_copyrights(self, copyrights):
        ret = []
        ret.append("---\nlegal:\n    copyrights:\n")
        prefix = "       "
        max_line = 75
        max_length = max_line - len(prefix)
        for c_line in copyrights:
            if (len(prefix) + len(c_line)) > max_line:
                ret.append(prefix + " - ")
                lines = [c_line[i:i+max_length] for i in range(0, len(c_line), max_length)]
                first = True
                for line in lines:
                    if first:
                        ret.append(line + "\n")
                        first = False
                    else:
                        ret.append(prefix + "   " + line + "\n")

            else:
                ret.append(prefix + " - " + c_line + "\n")
        return "".join(ret)
