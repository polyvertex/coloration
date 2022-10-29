# Copyright (c) Jean-Charles Lefebvre
# SPDX-License-Identifier: MIT

import re


#: A strict codec (i.e. ``ascii``) used for the encoding and decoding of ANSI
#: escape sequences.
#:
#: ..seealso:: `ANSI_ENCODING_ERRORS`, `ansi_encode()`, `ansi_decode()`
ANSI_ENCODING = "ascii"

#: Strict error handling (i.e. ``strict``) used for the encoding and decoding of
#: ANSI escape sequences
#:
#: ..seealso:: `ANSI_ENCODING`, `ansi_encode()`, `ansi_decode()`
ANSI_ENCODING_ERRORS = "strict"


#: Regular expression to find a full Control Sequence (CSI) or an Operating
#: System Command (OSC) from a `str` object.
#:
#: The first captured group of the resulting `re.Match` object is always the
#: introduction sequence (i.e. CSI or OSC).
ANSI_CODE_REGEX_STR = re.compile(
    r"""
        (?:
            # Control Sequence
            (?:
                \001*     # SOH
                (\033\[)  # CSI (MUST BE THE FIRST CAPTURED GROUP)
                (
                    ([\x30-\x3f]*)  # parameter bytes ([0-9:;<=>?])
                    ([\x20-\x2f]*)  # intermediate bytes ([\x20!"#$%&'()*+,-./])
                    ([\x40-\x7e])   # final byte ([@A-Z[\]^_`a-z{|}~])
                )
                \002*  # STX
            )
            |
            # Operating System Command
            (?:
                \001*           # SOH
                (\033\])        # OSC (MUST BE THE FIRST CAPTURED GROUP)
                ([^\007\002]*)
                [\007|\002]+    # BEL and/or STX
            )
        )
    """,
    re.A | re.VERBOSE)

#: Same as `ANSI_CODE_REGEX_STR` for `bytes` objects
ANSI_CODE_REGEX_BIN = re.compile(
    ANSI_CODE_REGEX_STR.pattern.encode(ANSI_ENCODING, ANSI_ENCODING_ERRORS),
    ANSI_CODE_REGEX_STR.flags)


#: Regular expression to find a Select Graphic Rendition (SGR) sequence that is
#: not (or does not end with) a RESET code
ANSI_NONRESET_SGR_REGEX_STR = re.compile(
    r"""
        \033\[             # CSI, not necessarily a SGR yet
        (?:[0-9]{1,5}\;)*  # SGR attr. can be joined in a same sequence...
        0*[1-9][0-9]*      # ... as long it does not end with a RESET code
        m                  # SGR termination
    """,
    re.A | re.VERBOSE)

#: Same as `ANSI_NONRESET_SGR_REGEX_STR` for `bytes` objects
ANSI_NONRESET_SGR_REGEX_BIN = re.compile(
    ANSI_NONRESET_SGR_REGEX_STR.pattern.encode(
        ANSI_ENCODING, ANSI_ENCODING_ERRORS),
    ANSI_NONRESET_SGR_REGEX_STR.flags)


#: Regular expression to match an end-of-string, or right before a sequence of
#: VT, FF, CR and/or LF characters
ANSI_AUTORESET_REGEX_STR = re.compile(
    r"""
        (?:
            ([\f\v\r\n]+)  # there are trailing whitespaces
            |
            (?<=[^\f\v\r\n])  # no trailing trailing whitespace
        )
        \Z  # EOS
    """,
    re.A | re.VERBOSE)

#: Same as `ANSI_AUTORESET_REGEX_STR` for `bytes` objects
ANSI_AUTORESET_REGEX_BIN = re.compile(
    ANSI_AUTORESET_REGEX_STR.pattern.encode(
        ANSI_ENCODING, ANSI_ENCODING_ERRORS),
    ANSI_AUTORESET_REGEX_STR.flags)


#: A `tuple` of the names of all the 256 8-bit colors
ANSI_8BIT_COLOR_NAMES = (
    "BLACK",  # 0
    "RED",  # 1
    "GREEN",  # 2
    "YELLOW",  # 3
    "BLUE",  # 4
    "MAGENTA",  # 5
    "CYAN",  # 6
    "LIGHT_GRAY",  # 7
    "DARK_GRAY",  # 8
    "LIGHT_RED",  # 9
    "LIGHT_GREEN",  # 10
    "LIGHT_YELLOW",  # 11
    "LIGHT_BLUE",  # 12
    "LIGHT_MAGENTA",  # 13
    "LIGHT_CYAN",  # 14
    "WHITE",  # 15
    "GREY_0",  # 16
    "NAVY_BLUE",  # 17
    "DARK_BLUE",  # 18
    "BLUE_3A",  # 19
    "BLUE_3B",  # 20
    "BLUE_1",  # 21
    "DARK_GREEN",  # 22
    "DEEP_SKY_BLUE_4A",  # 23
    "DEEP_SKY_BLUE_4B",  # 24
    "DEEP_SKY_BLUE_4C",  # 25
    "DODGER_BLUE_3",  # 26
    "DODGER_BLUE_2",  # 27
    "GREEN_4",  # 28
    "SPRING_GREEN_4",  # 29
    "TURQUOISE_4",  # 30
    "DEEP_SKY_BLUE_3A",  # 31
    "DEEP_SKY_BLUE_3B",  # 32
    "DODGER_BLUE_1",  # 33
    "GREEN_3A",  # 34
    "SPRING_GREEN_3A",  # 35
    "DARK_CYAN",  # 36
    "LIGHT_SEA_GREEN",  # 37
    "DEEP_SKY_BLUE_2",  # 38
    "DEEP_SKY_BLUE_1",  # 39
    "GREEN_3B",  # 40
    "SPRING_GREEN_3B",  # 41
    "SPRING_GREEN_2A",  # 42
    "CYAN_3",  # 43
    "DARK_TURQUOISE",  # 44
    "TURQUOISE_2",  # 45
    "GREEN_1",  # 46
    "SPRING_GREEN_2B",  # 47
    "SPRING_GREEN_1",  # 48
    "MEDIUM_SPRING_GREEN",  # 49
    "CYAN_2",  # 50
    "CYAN_1",  # 51
    "DARK_RED_1",  # 52
    "DEEP_PINK_4A",  # 53
    "PURPLE_4A",  # 54
    "PURPLE_4B",  # 55
    "PURPLE_3",  # 56
    "BLUE_VIOLET",  # 57
    "ORANGE_4A",  # 58
    "GREY_37",  # 59
    "MEDIUM_PURPLE_4",  # 60
    "SLATE_BLUE_3A",  # 61
    "SLATE_BLUE_3B",  # 62
    "ROYAL_BLUE_1",  # 63
    "CHARTREUSE_4",  # 64
    "DARK_SEA_GREEN_4A",  # 65
    "PALE_TURQUOISE_4",  # 66
    "STEEL_BLUE",  # 67
    "STEEL_BLUE_3",  # 68
    "CORNFLOWER_BLUE",  # 69
    "CHARTREUSE_3A",  # 70
    "DARK_SEA_GREEN_4B",  # 71
    "CADET_BLUE_2",  # 72
    "CADET_BLUE_1",  # 73
    "SKY_BLUE_3",  # 74
    "STEEL_BLUE_1A",  # 75
    "CHARTREUSE_3B",  # 76
    "PALE_GREEN_3A",  # 77
    "SEA_GREEN_3",  # 78
    "AQUAMARINE_3",  # 79
    "MEDIUM_TURQUOISE",  # 80
    "STEEL_BLUE_1B",  # 81
    "CHARTREUSE_2A",  # 82
    "SEA_GREEN_2",  # 83
    "SEA_GREEN_1A",  # 84
    "SEA_GREEN_1B",  # 85
    "AQUAMARINE_1A",  # 86
    "DARK_SLATE_GRAY_2",  # 87
    "DARK_RED_2",  # 88
    "DEEP_PINK_4B",  # 89
    "DARK_MAGENTA_1",  # 90
    "DARK_MAGENTA_2",  # 91
    "DARK_VIOLET_1A",  # 92
    "PURPLE_1A",  # 93
    "ORANGE_4B",  # 94
    "LIGHT_PINK_4",  # 95
    "PLUM_4",  # 96
    "MEDIUM_PURPLE_3A",  # 97
    "MEDIUM_PURPLE_3B",  # 98
    "SLATE_BLUE_1",  # 99
    "YELLOW_4A",  # 100
    "WHEAT_4",  # 101
    "GREY_53",  # 102
    "LIGHT_SLATE_GREY",  # 103
    "MEDIUM_PURPLE",  # 104
    "LIGHT_SLATE_BLUE",  # 105
    "YELLOW_4B",  # 106
    "DARK_OLIVE_GREEN_3A",  # 107
    "DARK_GREEN_SEA",  # 108
    "LIGHT_SKY_BLUE_3A",  # 109
    "LIGHT_SKY_BLUE_3B",  # 110
    "SKY_BLUE_2",  # 111
    "CHARTREUSE_2B",  # 112
    "DARK_OLIVE_GREEN_3B",  # 113
    "PALE_GREEN_3B",  # 114
    "DARK_SEA_GREEN_3A",  # 115
    "DARK_SLATE_GRAY_3",  # 116
    "SKY_BLUE_1",  # 117
    "CHARTREUSE_1",  # 118
    "LIGHT_GREEN_2",  # 119
    "LIGHT_GREEN_3",  # 120
    "PALE_GREEN_1A",  # 121
    "AQUAMARINE_1B",  # 122
    "DARK_SLATE_GRAY_1",  # 123
    "RED_3A",  # 124
    "DEEP_PINK_4C",  # 125
    "MEDIUM_VIOLET_RED",  # 126
    "MAGENTA_3A",  # 127
    "DARK_VIOLET_1B",  # 128
    "PURPLE_1B",  # 129
    "DARK_ORANGE_3A",  # 130
    "INDIAN_RED_1A",  # 131
    "HOT_PINK_3A",  # 132
    "MEDIUM_ORCHID_3",  # 133
    "MEDIUM_ORCHID",  # 134
    "MEDIUM_PURPLE_2A",  # 135
    "DARK_GOLDENROD",  # 136
    "LIGHT_SALMON_3A",  # 137
    "ROSY_BROWN",  # 138
    "GREY_63",  # 139
    "MEDIUM_PURPLE_2B",  # 140
    "MEDIUM_PURPLE_1",  # 141
    "GOLD_3A",  # 142
    "DARK_KHAKI",  # 143
    "NAVAJO_WHITE_3",  # 144
    "GREY_69",  # 145
    "LIGHT_STEEL_BLUE_3",  # 146
    "LIGHT_STEEL_BLUE",  # 147
    "YELLOW_3A",  # 148
    "DARK_OLIVE_GREEN_3",  # 149
    "DARK_SEA_GREEN_3B",  # 150
    "DARK_SEA_GREEN_2",  # 151
    "LIGHT_CYAN_3",  # 152
    "LIGHT_SKY_BLUE_1",  # 153
    "GREEN_YELLOW",  # 154
    "DARK_OLIVE_GREEN_2",  # 155
    "PALE_GREEN_1B",  # 156
    "DARK_SEA_GREEN_5B",  # 157
    "DARK_SEA_GREEN_5A",  # 158
    "PALE_TURQUOISE_1",  # 159
    "RED_3B",  # 160
    "DEEP_PINK_3A",  # 161
    "DEEP_PINK_3B",  # 162
    "MAGENTA_3B",  # 163
    "MAGENTA_3C",  # 164
    "MAGENTA_2A",  # 165
    "DARK_ORANGE_3B",  # 166
    "INDIAN_RED_1B",  # 167
    "HOT_PINK_3B",  # 168
    "HOT_PINK_2",  # 169
    "ORCHID",  # 170
    "MEDIUM_ORCHID_1A",  # 171
    "ORANGE_3",  # 172
    "LIGHT_SALMON_3B",  # 173
    "LIGHT_PINK_3",  # 174
    "PINK_3",  # 175
    "PLUM_3",  # 176
    "VIOLET",  # 177
    "GOLD_3B",  # 178
    "LIGHT_GOLDENROD_3",  # 179
    "TAN",  # 180
    "MISTY_ROSE_3",  # 181
    "THISTLE_3",  # 182
    "PLUM_2",  # 183
    "YELLOW_3B",  # 184
    "KHAKI_3",  # 185
    "LIGHT_GOLDENROD_2A",  # 186
    "LIGHT_YELLOW_3",  # 187
    "GREY_84",  # 188
    "LIGHT_STEEL_BLUE_1",  # 189
    "YELLOW_2",  # 190
    "DARK_OLIVE_GREEN_1A",  # 191
    "DARK_OLIVE_GREEN_1B",  # 192
    "DARK_SEA_GREEN_1",  # 193
    "HONEYDEW_2",  # 194
    "LIGHT_CYAN_1",  # 195
    "RED_1",  # 196
    "DEEP_PINK_2",  # 197
    "DEEP_PINK_1A",  # 198
    "DEEP_PINK_1B",  # 199
    "MAGENTA_2B",  # 200
    "MAGENTA_1",  # 201
    "ORANGE_RED_1",  # 202
    "INDIAN_RED_1C",  # 203
    "INDIAN_RED_1D",  # 204
    "HOT_PINK_1A",  # 205
    "HOT_PINK_1B",  # 206
    "MEDIUM_ORCHID_1B",  # 207
    "DARK_ORANGE",  # 208
    "SALMON_1",  # 209
    "LIGHT_CORAL",  # 210
    "PALE_VIOLET_RED_1",  # 211
    "ORCHID_2",  # 212
    "ORCHID_1",  # 213
    "ORANGE_1",  # 214
    "SANDY_BROWN",  # 215
    "LIGHT_SALMON_1",  # 216
    "LIGHT_PINK_1",  # 217
    "PINK_1",  # 218
    "PLUM_1",  # 219
    "GOLD_1",  # 220
    "LIGHT_GOLDENROD_2B",  # 221
    "LIGHT_GOLDENROD_2C",  # 222
    "NAVAJO_WHITE_1",  # 223
    "MISTY_ROSE1",  # 224
    "THISTLE_1",  # 225
    "YELLOW_1",  # 226
    "LIGHT_GOLDENROD_1",  # 227
    "KHAKI_1",  # 228
    "WHEAT_1",  # 229
    "CORNSILK_1",  # 230
    "GREY_100",  # 231
    "GREY_3",  # 232
    "GREY_7",  # 233
    "GREY_11",  # 234
    "GREY_15",  # 235
    "GREY_19",  # 236
    "GREY_23",  # 237
    "GREY_27",  # 238
    "GREY_30",  # 239
    "GREY_35",  # 240
    "GREY_39",  # 241
    "GREY_42",  # 242
    "GREY_46",  # 243
    "GREY_50",  # 244
    "GREY_54",  # 245
    "GREY_58",  # 246
    "GREY_62",  # 247
    "GREY_66",  # 248
    "GREY_70",  # 249
    "GREY_74",  # 250
    "GREY_78",  # 251
    "GREY_82",  # 252
    "GREY_85",  # 253
    "GREY_89",  # 254
    "GREY_93")  # 255

assert len(ANSI_8BIT_COLOR_NAMES) == 256
