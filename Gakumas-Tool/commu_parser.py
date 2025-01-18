import re


class ParsingString:
    def __init__(self, string: str):
        self.string = string

    def retrieve(self, pattern: re.Pattern[str] | str):
        # Attempts to match the string with the pattern
        # Removes the whole match from the string,
        # and returns the first group of the match
        # Note re.match only matches the start of the string
        match = re.match(pattern, self.string)
        if not match:
            raise Exception()
        self.string = self.string[match.end() :]
        return match.group(1)

    def peek(self, pattern: re.Pattern[str] | str):
        match = re.match(pattern, self.string)
        return bool(match)

    def is_empty(self):
        return self.string == ""


class Property:
    def __init__(self, data):
        self.data = data

    def __str__(self):
        return str(self.data)


class GroupProperty(Property):
    def __init__(self, data: "CommuGroup"):
        super().__init__(data)


class JsonProperty(Property):
    def __init__(self, data: str):
        super().__init__(data)


class StringProperty(Property):
    def __init__(self, data: str):
        super().__init__(data)

    def __str__(self):
        return escape_string(self.data)


class CommuGroup:
    def __init__(self, group_type: str):
        self.group_type = group_type
        self.property_pairs: list[tuple[str, Property]] = []

    def append_property(self, key: str, property: Property):
        self.property_pairs.append((key, property))

    def get_property(self, key: str, defaultValue):
        found_properties = [
            pair[1].data for pair in self.property_pairs if pair[0] == key
        ]
        if len(found_properties) == 1:
            return found_properties[0]
        elif len(found_properties) == 0:
            return defaultValue
        else:
            raise Exception(f"More than one property with key '{key}' found in group!")

    def get_property_list(self, key: str):
        return [pair[1].data for pair in self.property_pairs if pair[0] == key]

    def modify_property(self, key: str, property: Property):
        self.property_pairs = [
            (key, property) if pair[0] == key else pair for pair in self.property_pairs
        ]

    @classmethod
    def from_commu_line(cls, text_to_parse: str):
        parsing_string = ParsingString(text_to_parse.strip())
        group = parse_group(parsing_string)
        if not parsing_string.is_empty():
            raise Exception()
        return group

    def __str__(self):
        parts = [self.group_type] + [
            f"{key}={property}" for (key, property) in self.property_pairs
        ]
        return "[" + " ".join(parts) + "]"


def unescape_string(string: str):
    return string.replace("\\n", "\n")


def escape_string(string: str):
    return string.replace("\n", "\\n")


def parse_group_type(parsing_string: ParsingString):
    return parsing_string.retrieve(r"([a-z]+)(?=[ \]])")


# This function gobbles up the = as well!
def parse_key(parsing_string: ParsingString):
    return parsing_string.retrieve(r"([A-Za-z]+)=")


def parse_string_data(parsing_string: ParsingString):
    # The first match-group consists of any character except
    # linebreak, backslash, square brackets, and equals, unless they are
    # in the combinations '\n' or '\='
    return parsing_string.retrieve(r"((?:[^\n\\\[\]=]|\\n|\\=)+)(?=[ \]])")


def parse_json_data(parsing_string: ParsingString):
    return parsing_string.retrieve(r"(\\\{\S+\\\})(?=[ \]])")


def parse_animation_curve_json_data(parsing_string: ParsingString):
    return parsing_string.retrieve(r"(AnimationCurve::\\\{\S+\\\})(?=[ \]])")


def parse_group(parsing_string: ParsingString) -> CommuGroup:
    parsing_string.retrieve(r"(\[)")
    group_type = parse_group_type(parsing_string)
    group = CommuGroup(group_type)
    while not parsing_string.peek(r"\]"):
        parsing_string.retrieve(r"( )")
        key = parse_key(parsing_string)
        property: Property
        if parsing_string.peek(r"\["):
            property = GroupProperty(parse_group(parsing_string))
        elif parsing_string.peek(r"AnimationCurve::\\\{"):
            property = JsonProperty(parse_animation_curve_json_data(parsing_string))
        elif parsing_string.peek(r"\\\{"):
            property = JsonProperty(parse_json_data(parsing_string))
        else:
            property = StringProperty(
                unescape_string(parse_string_data(parsing_string))
            )
        group.append_property(key, property)
    parsing_string.retrieve(r"(\])")
    return group
