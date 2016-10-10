/*
 *  regex.h
 *
 *  Regular expression library
 *
 *  Copyright (C) 2007 Mohammad Mohsenzadeh <mmohsenz@gmail.com>
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
 *  20 Jun 2007: Mohammad Mohsenzadeh <mmohsenz@gmail.com>
 *          - initial implementation of regex library
 */

#ifndef __REGEX_H__
#define __REGEX_H__

#define REG_BASIC    0
#define REG_EXTENDED 1
#define REG_ICASE    (REG_EXTENDED << 1)
#define REG_NEWLINE  (REG_ICASE << 1)
#define REG_NOSUB    (REG_NEWLINE << 1)

#define REG_NOTBOL 1
#define REG_NOTEOL (REG_NOTBOL << 1)
#define REG_STARTEND (REG_NOTEOL << 1)
#define REG_PARTIAL (REG_STARTEND << 1)

enum regex_errcode {
	REG_SUCCESS = 0,    /* successful operation */
	REG_PARMATCH,       /* obtained only partial match */
	REG_NOMATCH,        /* failed to match string */

	REG_BADPAT,         /* invalid regular expression pattern */
	REG_ECOLLATE,       /* invalid collation character */
	REG_ECTYPE,         /* invalid character class name */
	REG_EESCAPE,        /* invalid escape sequence */
	REG_ESUBREG,        /* invalid back reference */
	REG_EBRACK,         /* unbalanced brackets '[' or ']' */
	REG_EPAREN,         /* unbalanced paranthesis '(' or ')' */
	REG_EBRACE,         /* unbalanced braces '{' or '}' */
	REG_BADBR,          /* invalid contents of { } */
	REG_ERANGE,         /* invalid range end*/
	REG_ESPACE,         /* not enough memory space */
	REG_BADRPT,         /* invalid repetition operand */
	REG_EEND,           /* premature end of regular expression */
	REG_BIG,            /* regular expression too big */
	REG_ERRCODE_MAX
};
/*
enum {
    REG_BOL = 256,
    REG_EOL,
    REG_MAGIC
};
*/

#define REG_MAGIC 256

struct nfa;
struct dfa;

struct regex {

	/* compile options */
	unsigned long syntax;

	/* pointer to compiled nfa */
	struct nfa *nfa;

	/* pointer to compiled dfa */
	struct dfa *dfa;
};

struct regex_match {
	int rm_so;
	int rm_eo;
};

extern int regex_compile (struct regex *preg,
                          const char *pattern,
                          unsigned int pattern_len,
                          int cflags);

extern void regex_print (struct regex *preg);

extern int regex_match (const struct regex *preg,
                        const char *string,
                        unsigned int string_len,
                        unsigned int nmatch,
                        struct regex_match pmatch[],
                        int eflags);

extern int regex_error (int errcode, char *errbuf, unsigned int errbuf_size);


/* POSIX compatibility */
typedef enum regex_errcode reg_errcode_t;
typedef struct regex regex_t;
typedef struct regex_match regmatch_t;

#define regcomp(preg, pattern, cflags) \
	regex_compile(preg, pattern, strlen (pattern), cflags)

#define regexec(preg, string, nmatch, pmatch, eflags) \
	regex_match(preg, string, strlen (string), nmatch, pmatch, eflags)

#define regerror (errcode, preg, errbuf, errbuf_size) \
	regex_error(errcode, errbuf, errbuf_size)

#define regfree (preg) \
	regex_free(preg)

#endif /* __REGEX_H__ */

