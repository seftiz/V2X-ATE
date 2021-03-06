/*
 *  posix.c
 *
 *  POSIX.2 test package for regex library
 *
 *  Copyright (C) 2007 Mohammad Mohsenzadeh <mmohsenz@gmail.com> and
 *                     James Goruk <james.goruk@gmail.com>
 *
 *  This library is free software; you can redistribute it and/or
 *  modify it under the terms of the GNU Lesser General Public
 *  License as published by the Free Software Foundation; either
 *  version 2.1 of the License, or (at your option) any later version.
 *
 *  This library is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 *  Lesser General Public License for more details.
 *
 *  You should have received a copy of the GNU Lesser General Public
 *  License along with this library; if not, write to the Free Software
 *  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA 
 *
 *
 *  05 Aug 2007: Mohammad Mohsenzadeh <mmohsenz@gmail.com>
 *          - Full test package for POSIX.2
 */

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "regex.h"

#define ARRAY_SIZE(x) (sizeof(x) / sizeof((x)[0]))

struct test_token {

	/* regular expression to test */
	char *pattern;

	/* test string */
	char *string;

	/* expected results */
	reg_errcode_t ret;
};

struct test_token posix_sub[] = {
	{"(a", NULL, REG_EPAREN},
	{"(a)", "a", 0},
	{"((a))", "a", 0},
	{"(a)(b)", "ab", 0},
	{"(((((((((((((((((((((((((((((((a)))))))))))))))))))))))))))))))", "a", 0},
	{"(a)*", "", 0},
	{"(a*)", "", 0},
	{"(a*)b", "b", 0},
	{"(a*)b", "ab", 0},
	{"((a*)b)*", "ab", 0},
	{"((a*)b)*", "ab", 0},
	{"((a*)b)*", "abb", 0},
	{"((a*)b)*", "aabab", 0},
	{"((a*)b)*", "abbab", 0},
	{"((a*)b)*", "abaabaaaab", 0},
	{"(ab)*", "", 0},
	{"(ab)*", "abab", 0},
	{"(ab)*", "xababx", 0},
	{"(a)*b", "b", 0},
	{"(a)*b", "a", REG_NOMATCH},
	{"(a)*b", "ab", 0},
	{"(a)*b", "aab", 0},
	{"(a)*a", "a", 0},
	{"(a)*a", "aa", 0},
	{"(a*)*b", "ab", 0},
	{"(a*)*b", "b", 0},
	{"(a*)*b", "xbx", 0},
	{"(a*)*b", "ab", 0},
	{"(a*)*b", "xabx", 0},
	{"(a*)*b", "aab", 0},
	{"(a*)a", "a", 0},
	{"(a*)a", "aa", 0},
	{"(a*)*a", "a", 0},
	{"(a*)*a", "xax", 0},
	{"(a*)*a", "aa", 0},
	{"(a*)*a", "xaax", 0},
	{"(a)*ab", "ab", 0},
	{"(a)*ab", "aab", 0},
	{"(a*)ab", "ab", 0},
	{"(a*)ab", "aab", 0},
	{"(a*)ab", "xaabx", 0},
	{"(a*)*ab", "ab", 0},
	{"(a*)*ab", "aab", 0},
	{"(a*)*b*c", "c", 0},
	{"(a)*(ab)*", "ab", 0},
	{"(a*)*(ab)*", "ab", 0},
	{"(a*b)*", "", 0},
	{"(a*b)*", "b", 0},
	{"(a*b)*", "baab", 0},
	{"(a*b*)*", "ab", 0},
	{"(a*b*)*", "a", 0},
	{"(a*b*)*", "ab", 0},
	{"(a*b*)*", "ba", 0},
	{"(a*b*)*", "aa", 0},
	{"(a*b*)*", "bb", 0},
	{"(a*b*)*", "aba", 0},
	{"(a*b*)b", "b", 0},
	{"((a*)*(b*)*)*", "", 0},
	{"((a*)*(b*)*)*", "aba", 0},
	{"((a*)(b*))*", "", 0},
	{"(c(c(a)*(b)*)*)*", "", 0},
	{"((a*)(b*))*", "aba", 0},
	{"((a)*(b)*)*", "", 0},
	{"((a)*(b)*)*", "aba", 0},
	{"(c(a)*(b)*)*", "", 0},
	{"(c(a)*(b)*)*", "c", 0},
	{"c((a)*(b)*)*", "c", 0},
	{"(((a)*(b)*)*)*", "", 0},
	{"(c(c(a)*(b)*)*)*", "", 0},
	{"((a)*b)*", "", 0},
	{"((a)*b)*", "abb", 0},
	{"((a)*b)*", "abbab", 0},
	{"(a*)*", "", 0},
	{"(a*)*", "aa", 0},
	{"((a*)*)*", "", 0},
	{"((a*)*)*", "a", 0},
	{"(ab*)*", "", 0},
	{"(ab*)*", "aa", 0},
	{"(ab*)*c", "c", 0},
	{"(ab*)*c", "abbac", 0},
	{"(ab*)*c", "abac", 0},
	{"(a*b)*c", "c", 0},
	{"(a*b)*c", "bbc", 0},
	{"(a*b)*c", "aababc", 0},
	{"(a*b)*c", "aabaabc", 0},
	{"((a*)b*)", "", 0},
	{"((a*)b*)", "a", 0},
	{"((a*)b*)", "b", 0},
	{"((a)*b*)", "", 0},
	{"((a)*b*)", "a", 0},
	{"((a)*b*)", "b", 0},
	{"((a)*b*)", "ab", 0},
	{"((a*)b*)c", "c", 0},
	{"((a)*b*)c", "c", 0},
	{"(a*b*)*", "", 0},
	{"(((a*))((b*)))*", "", 0},
	{"(c*((a*))d*((b*))e*)*", "", 0},
	{"((a)*b)*c", "c", 0},
	{"(((((ab)*))))", "", 0},
	{"((((((ab)*)))))", "", 0},
	{"(((((((ab)*))))))", "", 0},
	{"((((((((ab)*)))))))", "", 0},
	{"(((((((((ab)*))))))))", "", 0},
	{"((((((((((ab)*)))))))))", "", 0},
	{"(((((((((ab)*))))))))", "abab", 0},
	{"(a)", "", REG_NOMATCH},
	{"((a))", "b", REG_NOMATCH},
	{"(a)(b)", "ac", REG_NOMATCH},
	{"(ab)*", "acab", 0},
	{"(a*)*b", "c", REG_NOMATCH},
	{"(a*b)*", "baa", 0},
	{"(a*b)*", "baabc", REG_NOMATCH},
	{"(a*b*)*", "c", REG_NOMATCH},
	{"((a*)*(b*)*)*", "c", REG_NOMATCH},
	{"(a*)*", "ab", REG_NOMATCH},
	{"((a*)*)*", "ab", REG_NOMATCH},
	{"((a*)*)*", "b", REG_NOMATCH},
	{"(ab*)*", "abc", REG_NOMATCH},
	{"(ab*)*c", "abbad", REG_NOMATCH},
	{"(a*c)*b", "aacaacd", REG_NOMATCH},
	{"(a*)", "b", REG_NOMATCH},
	{"((a*)b*)", "c", REG_NOMATCH}
};

struct test_token posix_common[] = {
	{"", NULL, REG_EEND},
	{"abc", "abc", 0},
	{"abc", "ab", REG_NOMATCH},
	{"\\a", "a", REG_NOMATCH},
	{"\\0", "0", REG_NOMATCH},
	{"\\n", "\n", 0},
	{"a\\n", "a\n", 0},
	{"\\nb", "\nb", 0},
	{"a\\nb", "a\nb", 0},

	/* Special characters */
	{"\\{", "{", 0},
	{"\\^", "^", 0},
	{"\\.", ".", 0},
	{"\\[", "[", 0},
	{"\\$", "$", 0},
	{"\\\\", "\\", 0},
	{"\\", NULL, REG_EESCAPE},
	{"a\\", NULL, REG_EESCAPE},
	{"a*\\", NULL, REG_EESCAPE},

	/* Repitition (zero or more) */
	{"ab*", "a", 0},
	{"ab*", "abb", 0},
	{"a*", "aa", 0},
	{"a*b", "aab", 0},
	{"a*ab", "aab", 0},
	{"a**", NULL, REG_BADRPT},
	{"b*c", "b", REG_NOMATCH},

	/* Any character (.) */
	{".", "a", 0},
	{".", "\004", 0},
	{".", "\n", 0},
	{".", "", REG_NOMATCH},

	/* Bracket expression */
	{"[", NULL, REG_EBRACK},
	{"[^", NULL, REG_EBRACK},
	{"[a", NULL, REG_EBRACK},
	{"[]", NULL, REG_EBRACK},
	{"[]a", NULL, REG_EBRACK},
	{"a[]a", NULL, REG_EBRACK},
	{"[ab]", "a", 0},
	{"[ab]", "b", 0},
	{"[^ab]", "c", 0},
	{"[^a]", "\n", 0},
	{"[a]*a", "aa", 0},
	{"[[]", "[", 0},
	{"[]]", "]", 0},
	{"[.]", ".", 0},
	{"[*]", "*", 0},
	{"[\\]", "\\", 0},
	{"[\\(]", "(", 0},
	{"[\\)]", ")", 0},
	{"[^]]", "a", 0},
	{"[a^]", "^", 0},
	{"[a$]", "$", 0},
	{"[]a]", "]", 0},
	{"[a][]]", "a]", 0},
	{"[\n]", "\n", 0},
	{"[^a]", "\n", 0},
	{"[a-]", "a", 0},

	/* Character classes */
	{"[:alpha:]", "p", 0},
	{"[:alpha:]", "q", REG_NOMATCH},
	{"[[:alpha:]]", "a", 0},
	{"[[:alpha:]]", "z", 0},
	{"[[:alpha:]]", "A", 0},
	{"[[:alpha:]]", "Z", 0},
	{"[[:alpha:]]", "2", REG_NOMATCH},
	{"[[:upper:]]", "A", 0},
	{"[[:upper:]]", "Z", 0},
	{"[[:upper:]]", "a", REG_NOMATCH},
	{"[[:lower:]]", "a", 0},
	{"[[:lower:]]", "z", 0},
	{"[[:lower:]]", "A", REG_NOMATCH},
	{"[[:digit:]]", "0", 0},
	{"[[:digit:]]", "9", 0},
	{"[[:digit:]]", "0123456789", 0},
	{"[[:digit:]]", "a", REG_NOMATCH},
	{"[[:alnum:]]", "0", 0},
	{"[[:alnum:]]", "9", 0},
	{"[[:alnum:]]", "a", 0},
	{"[[:alnum:]]", "z", 0},
	{"[[:alnum:]]", "A", 0},
	{"[[:alnum:]]", "Z", 0},
	{"[[:alnum:]]", ":", REG_NOMATCH},
	{"[[:xdigit:]]", "0", 0},
	{"[[:xdigit:]]", "9", 0},
	{"[[:xdigit:]]", "a", 0},
	{"[[:xdigit:]]", "f", 0},
	{"[[:xdigit:]]", "A", 0},
	{"[[:xdigit:]]", "F", 0},
	{"[[:xdigit:]]", "g", REG_NOMATCH},
	{"[[:space:]]", " ", 0},
	{"[[:space:]]", "a", REG_NOMATCH},
	{"[[:print:]]", " ", 0},
	{"[[:print:]]", "~", 0},
	{"[[:print:]]", "\177", REG_NOMATCH},
	{"[[:punct:]]", ",", 0},
	{"[[:punct:]]", "a", REG_NOMATCH},
	{"[[:graph:]]", "!", 0},
	{"[[:graph:]]", "~", 0},
	{"[[:graph:]]", " ", REG_NOMATCH},
	{"[[:cntrl:]]", "\177", 0},
	{"[[:cntrl:]]", "a", REG_NOMATCH},
	{"[[:digit:]a]", "a", 0},
	{"[[:digit:]a]", "2", 0},
	{"[a[:digit:]]", "a", 0},
	{"[a[:digit:]]", "2", 0},
	{"[[:]", "[", 0},
	{"[:]", ":", 0},
	{"[[:a]", "[", 0},
	{"[[:alpha:a]", "[", 0},
	{"[[:", NULL, REG_EBRACK},
	{"[[:alpha:", NULL, REG_EBRACK},
	{"[[:alpha:]", NULL, REG_EBRACK},
	{"[[::]]", NULL, REG_ECTYPE},
	{"[[:a:]]", NULL, REG_ECTYPE},
	{"[[:alpo:]]", NULL, REG_ECTYPE},
	{"[[:a:]", NULL, REG_ECTYPE},
	{"[[:", NULL, REG_EBRACK},
	{"[[:", NULL, REG_EBRACK},

	/* Character ranges */
	{"[z-a]", NULL, REG_ERANGE},
	{"[a--]", NULL, REG_ERANGE},
	{"[[:digit:]-9]", NULL, REG_ERANGE},
	{"[a-[:digit:]]", NULL, REG_ERANGE},
	{"[a-", NULL, REG_EBRACK},
	{"[a-z", NULL, REG_EBRACK},
	{"[a-a]", "a", 0},
	{"[a-z]", "z", 0},
	{"[-a]", "-", 0},
	{"[-a]", "a", 0},
	{"[a-]", "-", 0},
	{"[a-]", "a", 0},
	{"[--@]", "@", 0},
	{"[%--a]", "%", 0},
	{"[%--a]", "-", 0},
	{"[a%--]", "%", 0},
	{"[a%--]", "-", 0},
	{"[%--a]", "a", 0},
	{"[a-c-f]", NULL, REG_ERANGE},
	{"[)-+--/]", NULL, REG_ERANGE},
	{"[a-z]", "2", REG_NOMATCH},
	{"[^-a]", "-", REG_NOMATCH},
	{"[^a-]", "-", REG_NOMATCH},
	{"[ab][cd]", "ac", 0},
	{"[ab][cd]", "ae", REG_NOMATCH},

	/* Anchors */
	{"^a", "a", 0},
	{"^", "", 0},
	{"$", "", 0},
	{"a$", "a", 0},
	{"^ab$", "ab", 0},
	{"^$", "", 0},
	{"^", "a", REG_NOMATCH},
	{"^a", "ba", REG_NOMATCH},
	{"$", "b", REG_NOMATCH},
	{"a$", "ab", REG_NOMATCH},
	{"^$", "a", REG_NOMATCH},
	{"^ab$", "a", REG_NOMATCH}
};

struct test_token posix_basic[] = {
	/* Special characters */
	{"*", NULL, REG_BADRPT},
	{"\\(*\\)", NULL, REG_BADRPT},
	{"\\(^*\\)", NULL, REG_BADRPT},
	{"**", NULL, REG_BADRPT},
	{"{", "{", 0},
	{"()", "()", 0},
	{"a+", "a+", 0},
	{"a?", "a?", 0},
	{"a|b", "a|b", 0},
	{"a|", "a|", 0},
	{"|a", "|a", 0},
	{"a||", "a||", 0},
	{"\\(|a\\)", "|a", 0},
	{"\\(a|\\)", "a|", 0},
	{"a\\+", "a+", REG_EESCAPE},
	{"a\\?", "a?", REG_EESCAPE},
	{"a\\|b", "a|b", REG_EESCAPE},
	{"^*", "*", REG_BADRPT},
	{"^+", "+", 0},
	{"^?", "?", 0},
	{"^{", "{", 0},

	/* Valid subexpressions (empty) in basic only */
	{"\\(\\)", NULL, REG_EEND},
	{"a\\(\\)b", NULL, REG_EEND},
	{"\\(\\(\\)\\)*", NULL, REG_EEND},
	{"a\\)", "a)", 0},
	{"\\(a\\", NULL, REG_EESCAPE},

	/* Anchors */
/*	{"a^", "a^", 0},
	{"$a", "$a", 0},
	{"$^", "$^", 0},
	{"$^*", "$^^", 0},
	{"\\($^\\)", "$^", 0},
	{"$*", "$$", 0},
	{"$\\{0,\\}", "$$", 0},
	{"^$*", "$$", 0},
	{"^$\\{0,\\}", "$$", 0},
	{"2^10", "2^10", 0},
	{"$HOME", "$HOME", 0},
	{"$1.35", "$1.35", 0},*/

	/* Repitition by braces */
	{"a\\{", NULL, REG_EBRACE},
	{"a\\{-1", NULL, REG_BADBR},
	{"a\\{4294967295", NULL, REG_BADBR},
	{"a\\{4294967295,", NULL, REG_BADBR},
	{"a\\{1,0", NULL, REG_BADBR},
	{"a\\{1", NULL, REG_EBRACE},
	{"a\\{0,", NULL, REG_EBRACE},
	{"a\\{0,1", NULL, REG_EBRACE},
	{"a\\{0,1}", NULL, REG_EBRACE},
	
	/* Backreferences */
	/* there is a lot more in here */
/*	{"\\(a\\)\\1", "ab", REG_NOMATCH},
	{"\\(a\\)\\1\\1", "aab", REG_NOMATCH},
	{"\\(a\\)\\(b\\)\\2\\1", "abab", REG_NOMATCH},
	{"\\(a\\(c\\)d\\)\\1\\2", "acdc", REG_NOMATCH},
	{"\\(a*b\\)\\1", "abaab", REG_NOMATCH},
	{"\\(a\\)\\1*", "aaaaaaaaaab", REG_NOMATCH},
	{"\\(\\(a\\)\\1\\)*", "aaa", REG_NOMATCH},
	{"\\(\\(a\\)\\2\\)*", "abaa", REG_NOMATCH},
	{"\\(\\(a\\)\\1\\)*", "a", REG_NOMATCH},
	{"\\(\\(a\\)\\2\\)\\1", "abaa", REG_NOMATCH},
	{"\\(\\(a*\\)\\2\\)\\1", "abaa"},
	{"\\1", NULL, REG_ESUBREG},
	{"\\(a\\)\\2", NULL, REG_ESUBREG},*/
};

struct test_token posix_extended[] = {
	{"a)", "a)", 0},
	
	/* Valid use of special characters.  */
	{"\\(a", "(a", 0},
	{"a\\+", "a+", 0},
	{"a\\?", "a?", 0},
	{"\\{a", "{a", 0},
	{"\\|a", "|a", 0},
	{"a\\|b", "a|b", 0},
	{"a\\|?", "a", 0},
	{"a\\|?", "a|", 0},
	{"a\\|*", "a", 0},
	{"a\\|*", "a||", 0},
	{"\\(*\\)", ")", 0},
	{"\\(*\\)", "(()", 0},
	{"a\\|+", "a|", 0},
	{"a\\|+", "a||", 0},
	{"\\(+\\)", "()", 0},
	{"\\(+\\)", "(()", 0},
	{"a\\||b", "a|", 0},
	{"\\(?\\)", ")", 0},
	{"\\(?\\)", "()", 0},
	{"a+", "a", 0},
	{"a+", "aa", 0},
	{"a?", "", 0},
	{"a?", "a", 0},

	/* Bracket expressions.  */
	{"[(]", "(", 0},
	{"[+]", "+", 0},
	{"[?]", "?", 0},
	{"[{]", "{", 0},
	{"[|]", "|", 0},

	/* Subexpressions.  */
	{"(a+)*", "", 0},
	{"(a+)*", "aa", 0},
	{"(a?)*", "", 0},
	{"(a?)*", "aa", 0},

	/* Invalid as intervals */
	{"{", "{", 0},
	{"^{", "{", 0},
	{"a|{", "{", 0},
	{"({)", "{", 0},
	{"a{", "a{", 0},
	{"a{}", "a{}", 0},
	{"a{-1", "a{-1", 0},
	{"a{-1}", "a{-1}", 0},
	{"a{0", "a{0", 0},            
	{"a{0,", "a{0,", 0}, 
	{"a{1,0", "a{1,0", 0},
	{"a{1,0}", "a{1,0}", 0},
	{"a{0,1", "a{0,1", 0},
	{"[a{0,1}]", "}", 0},
	{"a{1,3}{-1}", "aaa{-1}", 0},
	{"a{1,3}{2,1}", "aaa{2,1}", 0},
	{"a{1,3}{1,2", "aaa{1,2", 0},

	/* Valid consecutive repetitions.  */
	{"a*+", NULL, REG_BADRPT},
	{"a*?", NULL, REG_BADRPT},
	{"a++", NULL, REG_BADRPT},
	{"a+*", NULL, REG_BADRPT},
	{"a+?", NULL, REG_BADRPT},
	{"a??", NULL, REG_BADRPT},
	{"a?*", NULL, REG_BADRPT},
	{"a?+", NULL, REG_BADRPT},

	{"a{2}?", NULL, REG_BADRPT},
	{"a{2}+", NULL, REG_BADRPT},
	{"a{2}{2}", NULL, REG_BADRPT},

	{"(a?){0,3}b", "aaab", 0}, 
	{"(a+){0,3}b", "b", 0}, 
	{"(a+){0,3}b", "ab", 0},
	{"(a+){1,3}b", "aaab", 0}, 
	{"(a?){1,3}b", "aaab", 0},

	/* Alternatives.  */
	{"a|b", "a", 0},
	{"a|b", "b", 0},
	{"(a|b|c)", "a", 0},
	{"(a|b|c)", "b", 0},
	{"(a|b|c)", "c", 0},
	{"(a|b|c)*", "abccba", 0},

	{"(a(b*))|c", "a", 0},
	{"(a(b*))|c", "ab", 0},
	{"(a(b*))|c", "c", 0},
	{"(a+?*|b)", NULL, REG_BADRPT},
	{"(a+?*|b)*", NULL, REG_BADRPT},
	{"(a*|b)*", "bb", 0},
	{"((a*)|b)*", "bb", 0},
	{"(a{0,}|b)*", "bb", 0},
	{"((a{0,})|b)*", "bb", 0},

	{"(a+?*|b)c", "bc", 0},
	{"(a+?*|b)*c", "bbc", 0},
	{"(a*|b)*c", "bbc", 0},
	{"((a*)|b)*c", "bbc", 0},
	{"(a{0,}|b)*c", "bbc", 0},
	{"((a{0,})|b)*c", "bbc", 0},
	{"((a{0,}\\b\\<)|b)", "b", 0},
	{"((a{0,}\\b\\<)|b)*", "b", 0},
	{"((a+?*{0,1}\\b\\<)|b)", "b", 0},
	{"((a+?*{0,2}\\b\\<)|b)", "b", 0},
	{"((a+?*{0,4095}\\b\\<)|b)", "b", 0},
	{"((a+?*{0,5119}\\b\\<)|b)", "b", 0},
	{"((a+?*{0,6143}\\b\\<)|b)", "b", 0},
	{"((a+?*{0,8191}\\b\\<)|b)", "b", 0},
	{"((a+?*{0,16383}\\b\\<)|b)", "b", 0},
	{"((a+?*{0,}\\b\\<)|b)", "b", 0},
	{"((a+?*{0,}\\b\\<)|b)*", "b", 0},
	{"((a+?*{0,}\\b\\<)|b)*", "bb", 0},

	{"(a*|b*)*c", "c", 0},	
	{"(a*|b*)*c", "ac", 0},
	{"(a*|b*)*c", "aac", 0},
	{"(a*|b*)*c", "bbc", 0},
	{"(a*|b*)*c", "abc", 0},
	{"(a*|b*)c", "c", 0},
	{"(a*|b*)c", "ac", 0},
	{"(a*|b*)c", "bc", 0},
	{"(a*|b*)c", "aac", 0},
	{"(a|b)*c", "ac", 0},
	{"(a|b)*c", "bc", 0},
	{"(a|b)*c", "abc", 0},
	{"(a*|b*)c", "bbc", 0},

	/* Complicated second alternative.  */
	{"(a*|(b*)*)*c", "bc", 0},
	{"(a*|(b*|c*)*)*d", "bd", 0},
	{"(a*|(b*|c*)*)*d", "bbd", 0},
	{"(a*|(b*|c*)*)*d", "cd", 0},
	{"(a*|(b*|c*)*)*d", "ccd", 0},
	{"(a*|b*|c*)*d", "aad", 0},
	{"(a*|b*|c*)*d", "bbd", 0},
	{"(a*|b*|c*)*d", "ccd", 0},

	/* Valid anchoring.  */
	{"a|^b", "b", 0},
	{"a|b$", "b", 0},
	{"^b|a", "b", 0},
	{"b$|a", "b", 0},
	{"(^a)", "a", 0},
	{"(a$)", "a", 0},

	/* Backtracking.  */
	/* Per POSIX D11.1 p. 108, leftmost longest match.  */
	{"(wee|week)(knights|night)", "weeknights", 0},
	{"(fooq|foo)qbar", "fooqbar", 0},
	{"(fooq|foo)(qbarx|bar)", "fooqbarx", 0},
	{"(fooq|foo)*qbar", "fooqbar", 0},
	{"(fooq|foo)*(qbar)", "fooqbar", 0},
	{"(fooq|foo)*(qbar)*", "fooqbar", 0}, 
	{"(fooq|fo|o)*qbar", "fooqbar", 0},
	{"(fooq|fo|o)*(qbar)", "fooqbar", 0},
	{"(fooq|fo|o)*(qbar)*", "fooqbar", 0},
	{"(fooq|fo|o)*(qbar|q)*", "fooqbar", 0},
	{"(fooq|foo)*(qbarx|bar)", "fooqbarx", 0},
	{"(fooq|foo)*(qbarx|bar)*", "fooqbarx", 0},
	{"(fooq|fo|o)+(qbar|q)+", "fooqbar", 0},
	{"(fooq|foo)+(qbarx|bar)", "fooqbarx", 0},
	{"(fooq|foo)+(qbarx|bar)+", "fooqbarx", 0},
	{"(foo|foobarfoo)(bar)*", "foobarfoo", 0},

	/* Combination.  */
	{"[ab]?c", "ac", 0},
	{"[ab]*c", "ac", 0},
	{"[ab]+c", "ac", 0},
	{"(a|b)?c", "ac", 0},
	{"(a|b)*c", "ac", 0},
	{"(a|b)+c", "ac", 0},
	{"(a*c)?b", "b", 0},
	{"(a*c)+b", "aacb", 0},
	{"a((b)|(c))d", "acd", 0},

	{"a^", NULL, 0},
	{"a^b", NULL, 0},
	{"$a", NULL, 0},
	{"a$b", NULL, 0},
	{"foo^bar", NULL, 0},
	{"foo$bar", NULL, 0},
	{"(^)", NULL, 0},
	{"($)", NULL, 0},
	{"(^$)", NULL, 0},
	{"\\(^a\\)", NULL, 0},
	{"a\\|^b", NULL, 0},
	{"\\w^a", NULL, 0},
	{"\\W^a", NULL, 0},
	{"(a^)", NULL, 0},
	{"($a)", NULL, 0},
	{"a(^b)", NULL, 0},
	{"a$(b)", NULL, 0},
	{"(a)^b", NULL, 0},
	{"(a)$b", NULL, 0},
	{"(a)(^b)", NULL, 0},
	{"(a$)(b)", NULL, 0},
	{"(a|b)^c", NULL, 0},
	{"(a|b)$c", NULL, 0},
	{"(a$|b)c", NULL, 0},
	{"(a|b$)c", NULL, 0},
	{"a(b|^c)", NULL, 0},
	{"a(^b|c)", NULL, 0},
	{"a$(b|c)", NULL, 0},
	{"(a)(^b|c)", NULL, 0},
	{"(a)(b|^c)", NULL, 0},
	{"(b$|c)(a)", NULL, 0},
	{"(b|c$)(a)", NULL, 0},
	{"(a(^b|c))", NULL, 0},
	{"(a(b|^c))", NULL, 0},
	{"((b$|c)a)", NULL, 0},
	{"((b|c$)a)", NULL, 0},
	{"((^a|^b)^c)", NULL, 0},
	{"(c$(a$|b$))", NULL, 0},
	{"((^a|^b)^c)", NULL, 0},
	{"((a$|b$)c)", NULL, 0},
	{"(c$(a$|b$))", NULL, 0},
	{"((^a|^b)|^c)^d", NULL, 0},
	{"((a$|b$)|c$)d$", NULL, 0},
	{"d$(c$|(a$|b$))", NULL, 0},
	{"((^a|^b)|^c)(^d)", NULL, 0},
	{"((a$|b$)|c$)(d$)", NULL, 0},
	{"(d$)((a$|b$)|c$)", NULL, 0},
	{"((^a|^b)|^c)((^d))", NULL, 0},
	{"((a$|b$)|c$)((d$))", NULL, 0},
	{"((d$))((a$|b$)|c$)", NULL, 0},
	{"(((^a|^b))c|^d)^e", NULL, 0},
	{"(((a$|b$))c|d$)$e$", NULL, 0},
	{"e$(d$|c((a$|b$)))", NULL, 0},
	{"(^a)((^b))", NULL, 0},
	{"(a$)((b$))", NULL, 0},
	{"((^a))(^b)", NULL, 0},
	{"((a$))(b$)", NULL, 0},
	{"((^a))((^b))", NULL, 0},
	{"((a$))((b$))", NULL, 0},
	{"((^a)^b)", NULL, 0},
	{"((a$)b$)", NULL, 0},
	{"(b$(a$))", NULL, 0},
	{"(((^a)b)^c)", NULL, 0},
	{"(((a$)b)c$)", NULL, 0},
	{"(c$(b(a$)))", NULL, 0},
	{"(((^a)b)c)^d", NULL, 0},
	{"(((a$)b)c)d$", NULL, 0},
	{"d$(c(b(a$)))", NULL, 0},
	{".^a", NULL, 0},
	{"a$.", NULL, 0},
	{"[a]^b", NULL, 0},
	{"b$[a]", NULL, 0},
	{"\\(a$\\)", NULL, 0},
	{"a$\\|b", NULL, 0},
	{"(^a|^b)^c", NULL, 0},
	{"c$(a$|b$)", NULL, 0},
	{"(^a|^b)^|^c", NULL, 0},
	{"(a$|b$)$|$c$", NULL, 0},
	{"(a$|$b$)$|c$", NULL, 0},
	{"($a$|b$)$|c$", NULL, 0},
	{"$(a$|b$)$|c$", NULL, 0},
	{"^c|d(^a|^b)", NULL, 0},
	{"(^a|^b)|d^c", NULL, 0},
	{"c$|(a$|b$)d", NULL, 0},
	{"c$d|(a$|b$)", NULL, 0},
	{"c(^a|^b)|^d", NULL, 0},
	{"(a$|b$)c|d$", NULL, 0},
	{"c(((^a|^b))|^d)e", NULL, 0},
	{"(c((^a|^b))|^d)e", NULL, 0},
	{"((c(^a|^b))|^d)e", NULL, 0},
	{"(((^a|^b))|c^d)e", NULL, 0},
	{"(((^a|^b))|^d)^e", NULL, 0},
	{"(c$((a|b))|d)e$", NULL, 0},
	{"(c((a$|b$))|d)e$", NULL, 0},
	{"(c((a|b)$)|d)e$", NULL, 0},
	{"(c((a|b))|d$)e$", NULL, 0},
	{"^d(^c|e((a|b)))", NULL, 0},
	{"^d(c|^e((a|b)))", NULL, 0},
	{"^d(c|e(^(a|b)))", NULL, 0},
	{"^d(c|e((^a|b)))", NULL, 0},
	{"^d(c|e((a|^b)))", NULL, 0},
	{"^d(c|e((a|b^)))", NULL, 0},
	{"^d(c|e((a|b)^))", NULL, 0},
	{"^d(c|e((a|b))^)", NULL, 0},
	{"^d(c|e((a|b)))^", NULL, 0},
	{"d$(c$|e((a$|b$)))", NULL, 0},
	{"d(c$|e$((a$|b$)))", NULL, 0},
	{"(((^a|^b))^c)|^de", NULL, 0},
	{"(((^a|^b))c)|^d^e", NULL, 0},
	{"(((a$|b))c$)|de$", NULL, 0},
	{"(((a|b$))c$)|de$", NULL, 0},
	{"(((a|b))c$)|d$e$", NULL, 0},
	{"^d^e|^(c((a|b)))", NULL, 0},
	{"^de|^(c^((a|b)))", NULL, 0},
	{"^de|^(c(^(a|b)))", NULL, 0},
	{"^de|^(c((^a|b)))", NULL, 0},
	{"^de|^(c((a|^b)))", NULL, 0},
	{"^de|(^c(^(a|b)))", NULL, 0},
	{"^de|(^c((^a|b)))", NULL, 0},
	{"^de|(^c((a|^b)))", NULL, 0},
	{"de$|(c($(a|b)$))", NULL, 0},
	{"de$|(c$((a|b)$))", NULL, 0},
	{"de$|($c((a|b)$))", NULL, 0},
	{"de$|$(c((a|b)$))", NULL, 0},
	{"de$|(c($(a|b))$)", NULL, 0},
	{"de$|(c$((a|b))$)", NULL, 0},
	{"de$|$(c((a|b))$)", NULL, 0},
	{"de$|(c($(a|b)))$", NULL, 0},
	{"de$|(c$((a|b)))$", NULL, 0},
	{"de$|($c((a|b)))$", NULL, 0},
	{"de$|$(c((a|b)))$", NULL, 0},
	{"^a(^b|c)|^d", NULL, 0},
	{"^a(b|^c)|^d", NULL, 0},
	{"^a(b|c^)|^d", NULL, 0},
	{"^a(b|c)^|^d", NULL, 0},
	{"a$(b$|c$)|d$", NULL, 0},
	{"^d|^a(^b|c)", NULL, 0},
	{"^d|^a(b|^c)", NULL, 0},
	{"d$|a$(b$|c$)", NULL, 0},
	{"^d|^(b|c)^a", NULL, 0},
	{"d$|(b|c$)a$", NULL, 0},
	{"d$|(b$|c)a$", NULL, 0},
	{"^(a)^(b|c)|^d", NULL, 0},
	{"^(a)(^b|c)|^d", NULL, 0},
	{"^(a)(b|^c)|^d", NULL, 0},
	{"(a)$(b|c)$|d$", NULL, 0},
	{"(a$)(b|c)$|d$", NULL, 0},
	{"(^a)(^b|c)|^d", NULL, 0},
	{"(^a)(b|^c)|^d", NULL, 0},
	{"(a)$(b$|c$)|d$", NULL, 0},
	{"(a$)(b$|c$)|d$", NULL, 0},
	{"^d|^(b|c)^(a)", NULL, 0},
	{"^d|^(b|c)(^a)", NULL, 0},
	{"d$|(b|c$)(a)$", NULL, 0},
	{"d$|(b$|c)(a)$", NULL, 0},
	{"^d|(^b|^c)^(a)", NULL, 0},
	{"^d|(^b|^c)(^a)", NULL, 0},
	{"d$|(b|c)$(a$)", NULL, 0},
	{"d$|(b|c$)(a$)", NULL, 0},
	{"d$|(b$|c)(a$)", NULL, 0},
	{"^d|^(a)^(b|c)", NULL, 0},
	{"^d|^(a)(^b|c)", NULL, 0},
	{"^d|^(a)(b|^c)", NULL, 0},
	{"^d|(^a)^(b|c)", NULL, 0},
	{"^d|(^a)(^b|c)", NULL, 0},
	{"^d|(^a)(b|^c)", NULL, 0},
	{"d$|(a)$(b$|c$)", NULL, 0},
	{"d$|(a$)(b$|c$)", NULL, 0},
	{"((e^a|^b)|^c)|^d", NULL, 0},
	{"((^a|e^b)|^c)|^d", NULL, 0},
	{"((^a|^b)|e^c)|^d", NULL, 0},
	{"((^a|^b)|^c)|e^d", NULL, 0},
	{"d$e|(c$|(a$|b$))", NULL, 0},
	{"d$|(c$e|(a$|b$))", NULL, 0},
	{"d$|(c$|(a$e|b$))", NULL, 0},
	{"d$|(c$|(a$|b$e))", NULL, 0},
	{"d$|(c$|(a$|b$)e)", NULL, 0},
	{"d$|(c$|(a$|b$))e", NULL, 0},
	{"(a|b)^|c", NULL, 0},
	{"(a|b)|c^", NULL, 0},
	{"$(a|b)|c", NULL, 0},
	{"(a|b)|$c", NULL, 0},
	{"(a^|^b)|^c", NULL, 0},
	{"(^a|b^)|^c", NULL, 0},
	{"(^a|^b)|c^", NULL, 0},
	{"($a|b$)|c$", NULL, 0},
	{"(a$|$b)|c$", NULL, 0},
	{"(a$|b$)|$c", NULL, 0},
	{"c^|(^a|^b)", NULL, 0},
	{"^c|(a^|^b)", NULL, 0},
	{"^c|(^a|b^)", NULL, 0},
	{"$c|(a$|b$)", NULL, 0},
	{"c$|($a|b$)", NULL, 0},
	{"c$|(a$|$b)", NULL, 0},
	{"c^|^(a|b)", NULL, 0},
	{"^c|(a|b)^", NULL, 0},
	{"$c|(a|b)$", NULL, 0},
	{"c$|$(a|b)", NULL, 0},
	{"(a^|^b)c|^d", NULL, 0},
	{"(^a|b^)c|^d", NULL, 0},
	{"(^a|^b)c|d^", NULL, 0},
	{"(^a|^b)^c|^d", NULL, 0},
	{"(a|b)c$|$d", NULL, 0},
	{"(a|b)$c$|d$", NULL, 0},
	{"(a|b)$c$|d$", NULL, 0},
	{"(a|b$)c$|d$", NULL, 0},
	{"(a$|b)c$|d$", NULL, 0},
	{"($a|b)c$|d$", NULL, 0},
	{"$(a|b)c$|d$", NULL, 0},
	{"^d|^c^(a|b)", NULL, 0},
	{"^d|^c(^a|b)", NULL, 0},
	{"^d|^c(a|^b)", NULL, 0},
	{"^d|^c(a|b^)", NULL, 0},
	{"^d|^c(a|b)^", NULL, 0},
	{"$d|c(a$|b$)", NULL, 0},
	{"d$|c($a$|b$)", NULL, 0},
	{"d$|c$(a$|b$)", NULL, 0},
	{"d$|$c(a$|b$)", NULL, 0},
	
	{"(((a^|^b))c|^d)e", NULL, 0},
	{"(((^a|b^))c|^d)e", NULL, 0},
	{"(((^a|^b))^c|^d)e", NULL, 0},
	{"((^(a|b))c|d^)e", NULL, 0},
	{"(^((a|b))c|^d)^e", NULL, 0},
	{"(^((a|b)^)c|^d)e", NULL, 0},
	{"(^((a^|b))c|^d)e", NULL, 0},
	{"(^((a|b^))c|^d)e", NULL, 0},
	{"(^((a|b)^)c|^d)e", NULL, 0},
	{"(^((a|b))^c|^d)e", NULL, 0},
	{"(^((a|b))c^|^d)e", NULL, 0},
	{"(^((a|b))c|^d^)e", NULL, 0},
	{"(^((a|b))c|^d)^e", NULL, 0},
	{"(((a|b))c|d)$e$", NULL, 0},
	{"(((a|b))c|d$)e$", NULL, 0},
	{"(((a|b))c|$d)e$", NULL, 0},
	{"(((a|b))c$|d)e$", NULL, 0},
	{"(((a|b))$c|d)e$", NULL, 0},
	{"(((a|b)$)c|d)e$", NULL, 0},
	{"(((a|b$))c|d)e$", NULL, 0},
	{"(((a$|b))c|d)e$", NULL, 0},
	{"((($a|b))c|d)e$", NULL, 0},
	{"(($(a|b))c|d)e$", NULL, 0},
	{"($((a|b))c|d)e$", NULL, 0},
	{"$(((a|b))c|d)e$", NULL, 0},
	{"(^((a|b)^)c|^d)e", NULL, 0},
	{"(^((a|b))^c|^d)e", NULL, 0},
	{"(^((a|b))c|^d^)e", NULL, 0},
	{"(^((a|b))c|^d)^e", NULL, 0},
	
	{"^e(^d|c((a|b)))", NULL, 0},
	{"^e(d|^c((a|b)))", NULL, 0},
	{"^e(d|c^((a|b)))", NULL, 0},
	{"^e(d|c(^(a|b)))", NULL, 0},
	{"^e(d|c((^a|b)))", NULL, 0},
	{"^e(d|c((a|^b)))", NULL, 0},
	{"^e(d|c((a|b^)))", NULL, 0},
	{"^e(d|c((a|b)^))", NULL, 0},
	{"^e(d|c((a|b))^)", NULL, 0},
	{"^e(d|c((a|b)))^", NULL, 0},
	{"e$(d$|c((a$|b$)))", NULL, 0},
	{"e(d$|c$((a$|b$)))", NULL, 0},
	{"e(d$|c($(a$|b$)))", NULL, 0},
	{"e(d$|c(($a$|b$)))", NULL, 0},
	{"e$(d$|c((a|b)$))", NULL, 0},
	{"e($d$|c((a|b)$))", NULL, 0},
	{"e(d$|$c((a|b)$))", NULL, 0},
	{"e(d$|c$((a|b)$))", NULL, 0},
	{"e(d$|c($(a|b)$))", NULL, 0},
	{"e(d$|c(($a|b)$))", NULL, 0},
	{"e(d$|c((a|$b)$))", NULL, 0},
	{"e(d$|c((a$|$b$)))", NULL, 0},
	
	{"e$(d$|c((a|b))$)", NULL, 0},
	{"e($d$|c((a|b))$)", NULL, 0},
	{"e(d$|$c((a|b))$)", NULL, 0},
	{"e(d$|c$((a|b))$)", NULL, 0},
	{"e(d$|c($(a|b))$)", NULL, 0},
	{"e(d$|c(($a|b))$)", NULL, 0},
	{"e(d$|c((a|$b))$)", NULL, 0},
	{"e$(d$|c((a|b)))$", NULL, 0},
	{"e($d$|c((a|b)))$", NULL, 0},
	{"e(d$|$c((a|b)))$", NULL, 0},
	{"e(d$|c$((a|b)))$", NULL, 0},
	{"e(d$|c($(a|b)))$", NULL, 0},
	{"e(d$|c(($a|b)))$", NULL, 0},
	{"e(d$|c((a|$b)))$", NULL, 0},
	{"(((^a|^b)^)c)|^de", NULL, 0},
	{"(((^a|^b))^c)|^de", NULL, 0},
	{"(((^a|^b))c)^|^de", NULL, 0},
	{"$(((a|b))c$)|de$", NULL, 0},
	{"($((a|b))c$)|de$", NULL, 0},
	{"(($(a|b))c$)|de$", NULL, 0},
	{"((($a|b))c$)|de$", NULL, 0},
	{"(((a|$b))c$)|de$", NULL, 0},
	{"(((a|b)$)c$)|de$", NULL, 0},
	{"(((a|b))$c$)|de$", NULL, 0},
	{"$(((a|b))c)$|de$", NULL, 0},
	{"($((a|b))c)$|de$", NULL, 0},
	{"(($(a|b))c)$|de$", NULL, 0},
	{"((($a|b))c)$|de$", NULL, 0},
	{"(((a|$b))c)$|de$", NULL, 0},
	{"(((a|b)$)c)$|de$", NULL, 0},
	{"(((a|b))$c)$|de$", NULL, 0},
	{"^ed|^(c((a|b)))^", NULL, 0},
	{"^ed|^(c((a|b))^)", NULL, 0},
	{"^ed|^(c((a|b)^))", NULL, 0},
	{"^ed|^(c((a|b^)))", NULL, 0},
	{"^ed|^(c((a^|b)))", NULL, 0},
	{"^ed|^(c((^a|b)))", NULL, 0},
	{"^ed|^(c(^(a|b)))", NULL, 0},
	{"^ed|^(c^((a|b)))", NULL, 0},
	{"^ed|(^c((a|b)))^", NULL, 0},
	{"^ed|(^c((a|b))^)", NULL, 0},
	{"^ed|(^c((a|b)^))", NULL, 0},
	{"^ed|(^c((a|b^)))", NULL, 0},
	{"^ed|(^c((a|^b)))", NULL, 0},
	{"^ed|(^c((a^|b)))", NULL, 0},
	{"^ed|(^c((^a|b)))", NULL, 0},
	{"^ed|(^c(^(a|b)))", NULL, 0},
	{"^ed|(^c(^(a|b)))", NULL, 0},
	{"^ed|(^c^((a|b)))", NULL, 0},
	{"ed$|$(c((a|b)))$", NULL, 0},
	{"ed$|($c((a|b)))$", NULL, 0},
	{"ed$|(c$((a|b)))$", NULL, 0},
	{"ed$|(c($(a|b)))$", NULL, 0},
	{"ed$|(c(($a|b)))$", NULL, 0},
	{"ed$|(c((a|$b)))$", NULL, 0},
	{"ed$|$(c((a|b))$)", NULL, 0},
	{"ed$|($c((a|b))$)", NULL, 0},
	{"ed$|(c$((a|b))$)", NULL, 0},
	{"ed$|(c($(a|b))$)", NULL, 0},
	{"ed$|(c(($a|b))$)", NULL, 0},
	{"ed$|(c((a|$b))$)", NULL, 0},
	{"ed$|$(c((a|b)$))", NULL, 0},
	{"ed$|($c((a|b)$))", NULL, 0},
	{"ed$|(c$((a|b)$))", NULL, 0},
	{"ed$|(c($(a|b)$))", NULL, 0},
	{"ed$|(c(($a|b)$))", NULL, 0},
	{"ed$|(c((a|$b)$))", NULL, 0},
	{"ed$|$(c((a|b)$))", NULL, 0},
	{"ed$|($c((a|b)$))", NULL, 0},
	{"ed$|(c$((a|b)$))", NULL, 0},
	{"ed$|(c($(a|b)$))", NULL, 0},
	{"ed$|(c(($a|b)$))", NULL, 0},
	{"ed$|(c((a|$b)$))", NULL, 0},
	{"ed$|$(c((a|b)$))", NULL, 0},
	{"ed$|($c((a|b)$))", NULL, 0},
	{"ed$|(c$((a|b)$))", NULL, 0},
	{"ed$|(c($(a|b)$))", NULL, 0},
	{"ed$|(c(($a|b)$))", NULL, 0},
	{"ed$|(c((a|$b)$))", NULL, 0},
	{"ed$|$(c((a|b)$))", NULL, 0},
	{"ed$|($c((a|b)$))", NULL, 0},
	{"ed$|(c$((a|b)$))", NULL, 0},
	{"ed$|(c($(a|b)$))", NULL, 0},
	{"ed$|(c(($a|b)$))", NULL, 0},
	{"ed$|(c((a|$b)$))", NULL, 0},
	{"ed$|$(c((a|b)$))", NULL, 0},
	{"ed$|($c((a|b)$))", NULL, 0},
	{"ed$|(c$((a|b)$))", NULL, 0},
	{"ed$|(c($(a|b)$))", NULL, 0},
	{"ed$|(c(($a|b)$))", NULL, 0},
	{"ed$|(c((a|$b)$))", NULL, 0},
	{"ed$|$(c((a$|b$)))", NULL, 0},
	{"ed$|($c((a$|b$)))", NULL, 0},
	{"ed$|(c$((a$|b$)))", NULL, 0},
	{"ed$|(c($(a$|b$)))", NULL, 0},
	{"ed$|(c(($a$|b$)))", NULL, 0},
	{"ed$|(c((a$|$b$)))", NULL, 0},
	{"^a(b|c)^|^d", NULL, 0},
	{"^a(b|c^)|^d", NULL, 0},
	{"^a(b|^c)|^d", NULL, 0},
	{"^a(b^|c)|^d", NULL, 0},
	{"^a(^b|c)|^d", NULL, 0},
	{"^a^(b|c)|^d", NULL, 0},
	{"$a(b$|c$)|d$", NULL, 0},
	{"a$(b$|c$)|d$", NULL, 0},
	{"a($b$|c$)|d$", NULL, 0},
	{"a(b$|$c$)|d$", NULL, 0},
	{"a(b$|c$)|$d$", NULL, 0},
	{"^(a^)(b|c)|^d", NULL, 0},
	{"^(a)^(b|c)|^d", NULL, 0},
	{"^(a)(^b|c)|^d", NULL, 0},
	{"^(a)(b^|c)|^d", NULL, 0},
	{"^(a)(b|^c)|^d", NULL, 0},
	{"^(a)(b|c^)|^d", NULL, 0},
	{"^(a)(b|c)^|^d", NULL, 0},
	{"(^a^)(b|c)|^d", NULL, 0},
	{"(^a)^(b|c)|^d", NULL, 0},
	{"(^a)(^b|c)|^d", NULL, 0},
	{"(^a)(b^|c)|^d", NULL, 0},
	{"(^a)(b|^c)|^d", NULL, 0},
	{"(^a)(b|c^)|^d", NULL, 0},
	{"(^a)(b|c)^|^d", NULL, 0},
	
	{"(a)(b$|c$)d$", NULL, 0},
	{"(a)(b|$c)$|d$", NULL, 0},
	{"(a)($b|c)$|d$", NULL, 0},
	{"(a)$(b|c)$|d$", NULL, 0},
	{"(a$)(b|c)$|d$", NULL, 0},
	{"($a)(b|c)$|d$", NULL, 0},
	{"$(a)(b|c)$|d$", NULL, 0},
	{"(b|c)($a)$|d$", NULL, 0},
	{"(b|c)$(a)$|d$", NULL, 0},
	{"(b|c$)(a)$|d$", NULL, 0},
	{"(b|$c)(a)$|d$", NULL, 0},
	{"(b$|c)(a)$|d$", NULL, 0},
	{"($b|c)(a)$|d$", NULL, 0},
	{"$(b|c)(a)$|d$", NULL, 0},
	{"(b|c)($a$)|d$", NULL, 0},
	{"(b|c)$(a$)|d$", NULL, 0},
	{"(b|c$)(a$)|d$", NULL, 0},
	{"(b|$c)(a$)|d$", NULL, 0},
	{"(b$|c)(a$)|d$", NULL, 0},
	{"($b|c)(a$)|d$", NULL, 0},
	{"$(b|c)(a$)|d$", NULL, 0},
	{"(a)$(b$|c$)|d$", NULL, 0},
	{"(a$)(b$|c$)|d$", NULL, 0},
	{"($a)(b$|c$)|d$", NULL, 0},
	{"$(a)(b$|c$)|d$", NULL, 0},
	{"^d|^(b^|c)(a)", NULL, 0},
	{"^d|^(b|c^)(a)", NULL, 0},
	{"^d|^(b|c)^(a)", NULL, 0},
	{"^d|^(b|c)(^a)", NULL, 0},
	{"^d|^(b|c)(a^)", NULL, 0},
	{"^d|^(b|c)(a)^", NULL, 0},
	{"^d|(^b|^c^)(a)", NULL, 0},
	{"^d|(^b|^c)^(a)", NULL, 0},
	{"^d|(^b|^c)(^a)", NULL, 0},
	{"^d|(^b|^c)(a^)", NULL, 0},
	{"^d|(^b|^c)(a)^", NULL, 0},
	{"d$|(b|c)($a$)", NULL, 0},
	{"d$|(b|c)$(a$)", NULL, 0},
	{"d$|(b|c$)(a$)", NULL, 0},
	{"d$|(b$|c)(a$)", NULL, 0},
	{"d$|($b|c)(a$)", NULL, 0},
	{"d$|$(b|c)(a$)", NULL, 0},
	{"d$|(b|c)($a)$", NULL, 0},
	{"d$|(b|c)$(a)$", NULL, 0},
	{"d$|(b|c$)(a)$", NULL, 0},
	{"d$|(b$|c)(a)$", NULL, 0},
	{"d$|($b|c)(a)$", NULL, 0},
	{"d$|$(b|c)(a)$", NULL, 0},
	{"^d|^(a^)(b|c)", NULL, 0},
	{"^d|^(a)^(b|c)", NULL, 0},
	{"^d|^(a)(^b|c)", NULL, 0},
	{"^d|^(a)(b^|c)", NULL, 0},
	{"^d|^(a)(b|^c)", NULL, 0},
	{"^d|^(a)(b|c^)", NULL, 0},
	{"^d|^(a)(b|c)^", NULL, 0},
	{"^d|(^a^)(b|c)", NULL, 0},
	{"^d|(^a)^(b|c)", NULL, 0},
	{"^d|(^a)(^b|c)", NULL, 0},
	{"^d|(^a)(b^|c)", NULL, 0},
	{"^d|(^a)(b|^c)", NULL, 0},
	{"^d|(^a)(b|c^)", NULL, 0},
	{"^d|(^a)(b|c)^", NULL, 0},
	{"d$|(a)$(b$|c$)", NULL, 0},
	{"d$|(a$)(b$|c$)", NULL, 0},
	{"d$|($a)(b$|c$)", NULL, 0},
	{"d$|$(a)(b$|c$)", NULL, 0},
	{"d$|(a)(b|$c)$", NULL, 0},
	{"d$|(a)($b|c)$", NULL, 0},
	{"d$|(a)$(b|c)$", NULL, 0},
	{"d$|(a$)(b|c)$", NULL, 0},
	{"d$|($a)(b|c)$", NULL, 0},
	{"d$|$(a)(b|c)$", NULL, 0},
	{"((^a|^b)|^c)|^d^", NULL, 0},
	{"((^a|^b)|^c)^|^d", NULL, 0},
	{"((^a|^b)|^c^)|^d", NULL, 0},
	{"((^a|^b)^|^c)|^d", NULL, 0},
	{"((^a|^b^)|^c)|^d", NULL, 0},
	{"((^a^|^b)|^c)|^d", NULL, 0},
	{"((a|b)|c)|$d$", NULL, 0},
	{"((a|b)|$c)|d$", NULL, 0},
	{"((a|$b)|c)|d$", NULL, 0},
	{"(($a|b)|c)|d$", NULL, 0},
	{"($(a|b)|c)|d$", NULL, 0},
	{"$((a|b)|c)|d$", NULL, 0},
	{"^d^|(c|(a|b))", NULL, 0},
	{"^d|(c^|(a|b))", NULL, 0},
	{"^d|(c|(a^|b))", NULL, 0},
	{"^d|(c|(a|b^))", NULL, 0},
	{"^d|(c|(a|b)^)", NULL, 0},
	{"^d|(c|(a|b))^", NULL, 0},
	{"d$|(c$|(a$|$b$))", NULL, 0},
	{"d$|(c$|($a$|b$))", NULL, 0},
	{"d$|($c$|(a$|b$))", NULL, 0},
	{"d$|$(c$|(a$|b$))", NULL, 0},
	{"$d$|(c$|(a$|b$))", NULL, 0},
	{"d$|(c$|(a|$b)$)", NULL, 0},
	{"d$|(c$|($a|b)$)", NULL, 0},
	{"d$|($c$|(a|b)$)", NULL, 0},
	{"d$|$(c$|(a|b)$)", NULL, 0},
	{"$d$|(c$|(a|b)$)", NULL, 0},
	{"d$|(c$|(a|$b))$", NULL, 0},
	{"d$|(c$|($a|b))$", NULL, 0},
	{"d$|($c$|(a|b))$", NULL, 0},
	{"d$|$(c$|(a|b))$", NULL, 0},
	{"$d$|(c$|(a|b))$", NULL, 0},
	{"^c^|(^a|^b)", NULL, 0},
	{"^c|(^a^|^b)", NULL, 0},
	{"^c|(^a|^b^)", NULL, 0},
	{"^c|(^a|^b)^", NULL, 0},
	{"c$|(a$|$b$)", NULL, 0},
	{"c$|($a$|b$)", NULL, 0},
	{"c$|$(a$|b$)", NULL, 0},
	{"$c$|(a$|b$)", NULL, 0},
	{"^d^(c|e((a|b)))", NULL, 0},
	{"^d(^c|e((a|b)))", NULL, 0},
	{"^d(c^|e((a|b)))", NULL, 0},
	{"^d(c|^e((a|b)))", NULL, 0},
	{"^d(c|e^((a|b)))", NULL, 0},
	{"^d(c|e(^(a|b)))", NULL, 0},
	{"^d(c|e((^a|b)))", NULL, 0},
	{"^d(c|e((a|^b)))", NULL, 0},
	{"^d(c|e((a|b^)))", NULL, 0},
	{"^d(c|e((a|b)^))", NULL, 0},
	{"^d(c|e((a|b))^)", NULL, 0},
	{"^d(c|e((a|b)))^", NULL, 0},
	{"d(c$|e($(a$|b$)))", NULL, 0},
	{"d(c$|e$((a$|b$)))", NULL, 0},
	{"d(c$|$e((a$|b$)))", NULL, 0},
	{"d($c$|e((a$|b$)))", NULL, 0},
	{"d$(c$|e((a$|b$)))", NULL, 0},
	{"$d(c$|e((a$|b$)))", NULL, 0},
	{"^d|^a^(b|c)", NULL, 0},
	{"^d|^a(^b|c)", NULL, 0},
	{"^d|^a(b^|c)", NULL, 0},
	{"^d|^a(b|^c)", NULL, 0},
	{"^d|^a(b|c^)", NULL, 0},
	{"^d|^a(b|c)^", NULL, 0},
	{"d$|a($b$|c$)", NULL, 0},
	{"d$|a$(b$|c$)", NULL, 0},
	{"d$|$a(b$|c$)", NULL, 0},
	{"$d$|a(b$|c$)", NULL, 0},
	{"^d|^(b^|c)a", NULL, 0},
	{"^d|^(b|c^)a", NULL, 0},
	{"^d|^(b|c)^a", NULL, 0},
	{"^d|^(b|c)a^", NULL, 0},
	{"d$|(b|c)$a$", NULL, 0},
	{"d$|(b|c$)a$", NULL, 0},
	{"d$|(b|$c)a$", NULL, 0},
	{"d$|(b$|c)a$", NULL, 0},
	{"d$|($b|c)a$", NULL, 0},
	{"d$|$(b|c)a$", NULL, 0},
	{"$d$|(b|c)a$", NULL, 0},

	/* Invalid use of special characters.  */
	{"*", NULL, REG_BADRPT},
	{"a|*", NULL, REG_BADRPT},
	{"(*)", NULL, REG_BADRPT},
	{"^*", NULL, REG_BADRPT},
	{"+", NULL, REG_BADRPT},
	{"a|+", NULL, REG_BADRPT},
	{"(+)", NULL, REG_BADRPT},
	{"^+", NULL, REG_BADRPT},
	{"?", NULL, REG_BADRPT},
	{"a|?", NULL, REG_BADRPT},
	{"(?)", NULL, REG_BADRPT},
	{"^?", NULL, REG_BADRPT},
	{"|", NULL, REG_BADPAT},
	{"a|", NULL, REG_EEND},
	{"a||", NULL, REG_BADPAT},
	{"(|a)", NULL, REG_BADPAT},
	{"(a|)", NULL, REG_EEND},
	{"{1}", NULL, REG_BADRPT},
	{"a|{1}", NULL, REG_BADRPT},
	{"^{1}", NULL, REG_BADRPT},
	{"({1})", NULL, REG_BADRPT},
	{"|b", NULL, REG_BADPAT},
	{"^{0,}*", NULL, REG_BADRPT},
	{"$*", NULL, REG_BADRPT},
	{"${0,}*", NULL, REG_BADRPT},
	{"\\", NULL, REG_EESCAPE},

	{"a?b", "a", REG_NOMATCH},
	{"a+", "", REG_NOMATCH},
	{"a+b", "a", REG_NOMATCH},
	{"a?", "b", 0},

	/* Subexpressions.  */
	{"()", NULL, REG_EEND},
	{"a()", NULL, REG_EEND},
	{"()b", NULL, REG_EEND},
	{"a()b", NULL, REG_EEND},
	{"()*", NULL, REG_EEND},
	{"(()*", NULL, REG_EEND},

	/* Invalid intervals.  */
	{"a{2}*", "aaa", 0},
	{"a{2}?", "aaa", 0},
	{"a{2}+", "aaa", 0},
	{"a{2}{2}", "aaa", 0},
	{"a{1}{1}{2}", "aaa", 0},
	{"a{1}{1}{2}", "a", 0},
};

static void
test_match (unsigned int ntests, struct test_token *tests,
            char * (*translate)(char *dest, const char *src, size_t num),
            int cflags, int eflags)
{
	char pattern[1024];
	regex_t preg;
	int i, ret;
	
	for (i = 0; i < ntests; i++) {
		translate (pattern, tests[i].pattern, 512);

		ret = regcomp (&preg, pattern, cflags);

		if (tests[i].string && ret == 0)
			ret = regexec (&preg, tests[i].string, 0, NULL, eflags);

		printf ("%-32.32s %-32.32s %s\n", tests[i].pattern, tests[i].string,
				tests[i].ret == ret ? "[OK]" : "[FAILED]");
	}
}

static char *
translate_paren (char *dest, const char *src, size_t num)
{
	unsigned int length = strlen (src) + 1;
	int i, j;
	
	if (length > num)
		length = num - 1;
	
	for (i = 0, j = 0; i < length && j < num; i++) {
		if (src[i] == '(' || src[i] == ')')
			dest[j++] = '\\';
		dest[j++] = src[i];
	}
	return dest;
}

void
test_posix_basic (void)
{
	printf ("Starting POSIX Basic tests...\n");
	test_match (ARRAY_SIZE (posix_sub), posix_sub, translate_paren, 0, 0);
	test_match (ARRAY_SIZE (posix_common), posix_common, strncpy, 0, 0);
	test_match (ARRAY_SIZE (posix_basic), posix_basic, strncpy, 0, 0);
	printf ("Finished POSIX Basic tests.\n");
}

static inline void
test_posix_extended (void)
{
	printf ("Starting POSIX Extended tests...\n");
	test_match (ARRAY_SIZE (posix_sub), posix_sub, strncpy, REG_EXTENDED, 0);
	test_match (ARRAY_SIZE (posix_common), posix_common, strncpy, REG_EXTENDED, 0);
	test_match (ARRAY_SIZE (posix_extended), posix_extended, strncpy, REG_EXTENDED, 0);
	printf ("Finished POSIX Extended tests.\n");
}

int main (int argc, char **argv)
{
	test_posix_basic ();
	test_posix_extended ();
	return 0;
}
