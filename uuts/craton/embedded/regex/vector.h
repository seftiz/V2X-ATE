/*
 *  vector.h
 *
 *  Simple circular doubly linked list library
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
 *  02 Jul 2007: Mohammad Mohsenzadeh <mmohsenz@gmail.com>
 *          - initial implementation
 */

#ifndef __VECTOR_H__
#define __VECTOR_H__

struct vector_node {
	struct vector_node *next, *prev;
};

struct vector_head {
	struct vector_node *first, *last;
};

#define VECTOR_HEAD_INIT(name) \
	{ (struct vector_node *)&(name), (struct vector_node *)&(name) }

#define VECTOR_HEAD(name) \
	struct vector_head name = VECTOR_HEAD_INIT (name)

static inline void
vector_head_init (struct vector_head *head)
{
	head->first = (struct vector_node *)head;
	head->last = (struct vector_node *)head;
}

static inline void
__vector_add (struct vector_node *first,
              struct vector_node *last,
              struct vector_node *prev,
              struct vector_node *next)
{
	prev->next = first;
	first->prev = prev;
	last->next = next;
	next->prev = last;
}

#define vector_add(new, head) \
	__vector_add (new, new, (struct vector_node *)(head), (head)->first)

#define vector_add_tail(new, head) \
	__vector_add (new, new, (head)->last, (struct vector_node *)(head))

#define vector_addl(start, end, head) \
	__vector_add (start, end, (struct vector_node *)(head), (head)->first)

#define vector_addl_tail(start, end, head) \
	__vector_add (start, end, (head)->last, (struct vector_node *)(head))

static inline void
__vector_del (struct vector_node *first,
              struct vector_node *last)
{
	first->prev->next = last->next;
	last->next->prev = first->prev;
	first->prev = NULL;
	last->next = NULL;
}

#define vector_del(entry) __vector_del (entry, entry)

static inline void
__vector_move (struct vector_node *first,
               struct vector_node *last,
               struct vector_node *prev,
               struct vector_node *next)
{
	__vector_del (first, last);
	__vector_add (first, last, prev, next);
}

#define vector_move(entry, head) \
	__vector_move (entry, entry, (struct vector_node *)(head), (head)->first)

#define vector_move_tail(entry, head) \
	__vector_move (entry, entry, (head)->last, (struct vector_node *)(head))

#define vector_movel(start, end, head) \
	__vector_move (start, end, (struct vector_node *)(head), (head)->first)

#define vector_movel_tail(start, end, head) \
	__vector_move (start, end, (head)->last, (struct vector_node *)(head))

static inline int
vector_empty (const struct vector_head *head)
{
	return ((struct vector_node *)head == head->first);
}

#define container_of(ptr, type, member) \
	(type *)((char *)ptr - ((unsigned int) &((type *)0)->member))

#define vector_entry(ptr, type, member) \
	container_of (ptr, type, member)

#define vector_iterate(pos, head) \
	for (pos = (head)->first; pos != (struct vector_node *)(head); \
		pos = pos->next)

#define vector_iterate_reverse(pos, head) \
	for (pos = (head)->last; pos != (struct vector_node *)(head); \
		pos = pos->prev)

#define vector_iterate_safe(pos, n, head) \
	for (pos = (head)->first, n = pos->next; \
		pos != (struct vector_node *)(head); pos = n, n = pos->next)

#define vector_iterate_reverse_safe(pos, n, head) \
	for (pos = (head)->last, n = pos->prev; \
		pos != (struct vector_node *)(head); pos = n, n = pos->prev)

#define vector_iterate_entry(pos, head, member) \
	for (pos = container_of ((head)->first, typeof (*pos), member); \
		&pos->member != (struct vector_node *)(head); \
		pos = container_of (pos->member.next, typeof (*pos), member))

#define vector_iterate_entry_reverse(pos, head, member) \
	for (pos = container_of ((head)->last, typeof (*pos), member); \
		&pos->member != (struct vector_node *)(head); \
		pos = container_of (pos->member.prev, typeof (*pos), member))

#define vector_iterate_entry_safe(pos, n, head, member) \
	for (pos = container_of ((head)->first, typeof (*pos), member), \
			n = container_of (pos->member.next, typeof (*pos), member); \
		&pos->member != (struct vector_node *)(head); \
		pos = n, n = container_of (pos->member.next, typeof (*pos), member))

#define vector_iterate_entry_reverse_safe(pos, n, head, member) \
	for (pos = container_of ((head)->last, typeof (*pos), member), \
			n = container_of (pos->member.prev, typeof (*pos), member); \
		&pos->member != (struct vector_node *)(head); \
		pos = n, n = container_of (pos->member.prev, typeof (*pos), member))

#endif /* __VECTOR_H__ */

