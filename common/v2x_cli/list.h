#ifndef _ATLK_LIST_H
#define _ATLK_LIST_H

#include <atlk/sdk.h>

/*#if defined (__KERNEL__) || defined (__LINUX__)

#include <linux/list.h>

#else
	*/
/**
   @file
   Simple doubly linked list implementation.

   Some of the internal functions ("__xxx") are useful when
   manipulating whole lists rather than single entries, as
   sometimes we already know the next/prev entries and we can
   generate better code by using them directly rather than
   using the generic single-entry routines.
 
*/

/** Specific structure for link list manipulation in list.h file */
struct list_head {
  struct list_head *next, *prev;
};

#define LIST_POISON1 ((void*)0xDEADBE01)
#define LIST_POISON2 ((void*)0xDEADBE03)

#define LIST_HEAD_INVALID { LIST_POISON1, LIST_POISON2 }

#define LIST_HEAD_INIT(name) { &(name), &(name) }

#define LIST_HEAD(name) \
    struct list_head name = LIST_HEAD_INIT(name)

static inline void INIT_LIST_HEAD(struct list_head *list)
{
  list->next = list;
  list->prev = list;
}

static inline int list_invalid(struct list_head *list)
{
  return (list->next == LIST_POISON1 && list->prev == LIST_POISON2) ? 1 : 0;
}

/**
   Insert a new entry between two known consecutive entries.

   @param[in] new element 
   @param[in] prev element
   @param[in] next element

*/
static inline void __list_add(struct list_head *new,
            struct list_head *prev,
            struct list_head *next)
{
  next->prev = new;
  new->next = next;
  new->prev = prev;
  prev->next = new;
}

/**
   Add a new entry to list

   @param[in] new new entry  
   @param[in] head entries head list

*/
static inline void list_add(struct list_head *new, struct list_head *head)
{
  __list_add(new, head, head->next);
}

/**
   Add a new entry to list tail

   @param[in] new new  entry  
   @param[in] head entries head list

*/
static inline void list_add_tail(struct list_head *new, struct list_head *head)
{
  __list_add(new, head->prev, head);
}

/**
   Delete an entry from list

   @param[in] prev entry connected to target element 
   @param[in] next entry connected to target element

*/
static inline void __list_del(struct list_head * prev, struct list_head * next)
{
  next->prev = prev;
  prev->next = next;
}

/**
   Delete an entry from list

   @param[in] entry to be deleted from list 
*/
static inline void list_del(struct list_head *entry)
{
  __list_del(entry->prev, entry->next);
  entry->next =  LIST_POISON1;
  entry->prev =  LIST_POISON2;
}

/**
   Replace old entry by new one

   @param[in] old entry to be replaced with new entry
   @param[in] new entry to replace old entry 
*/
static inline void list_replace(struct list_head *old,
            struct list_head *new)
{
  new->next = old->next;
  new->next->prev = new;
  new->prev = old->prev;
  new->prev->next = new;
}

/**
   Replace old entry by new one and init the old list

   @param[in] old entry to be replaced with new entry
   @param[in] new entry to replace old entry 
*/
static inline void list_replace_init(struct list_head *old,
                struct list_head *new)
{
  list_replace(old, new);
  INIT_LIST_HEAD(old);
}

/**
   Deletes entry from list and reinitialize it.

   @param[in] entry the entry to delete from the list 
*/
static inline void list_del_init(struct list_head *entry)
{
  __list_del(entry->prev, entry->next);
  INIT_LIST_HEAD(entry);
}

/**
   Delete from one list and add as another's head

   @param[in] list the entry to move 
   @param[in] head the head that will precede our entry

*/
static inline void list_move(struct list_head *list, struct list_head *head)
{
  __list_del(list->prev, list->next);
  list_add(list, head);
}

/**
   Delete from one list and add as another's tail

   @param[in] list the entry to move 
   @param[in] head the head that will follow our entry

*/
static inline void list_move_tail(struct list_head *list,
              struct list_head *head)
{
  __list_del(list->prev, list->next);
  list_add_tail(list, head);
}

/**
   Tests whether *list is the last entry in list *head

   @param[in] list the entry to test 
   @param[in] head the head of the list

*/
static inline int list_is_last(const struct list_head *list,
            const struct list_head *head)
{
  return list->next == head;
}

/**
  Tests whether a list is empty
  @param[in] head: the list to test.
 */
static inline int list_empty(const struct list_head *head)
{
  return head->next == head;
}

/**
   Delete the first entry from list

   @param[in] head list head
   @param[out] pentry entry that was deleted or NULL in case of empty list
*/
static inline void
list_del_head(struct list_head *head, struct list_head **pentry)
{
  struct list_head *entry = NULL;

  if (!list_empty(head)) {
    entry = head->next;
    list_del(entry);
  }

  *pentry = entry;
}

/**
  Rotate the list to the left
  @param[in] head: the head of the list
 */
static inline void list_rotate_left(struct list_head *head)
{
  struct list_head *first;

  if (!list_empty(head)) {
    first = head->next;
    list_move_tail(first, head);
  }
}

/**
   Tests whether a list has just one entry.
   @param[in] head: the list to test.
 */
static inline int list_is_singular(const struct list_head *head)
{
  return !list_empty(head) && (head->next == head->prev);
}

static inline void __list_cut_position(struct list_head *list,
      struct list_head *head, struct list_head *entry)
{
  struct list_head *new_first = entry->next;
  list->next = head->next;
  list->next->prev = list;
  list->prev = entry;
  entry->next = list;
  head->next = new_first;
  new_first->prev = head;
}

/**
  Cut a list into two
  @param[in] list: a new list to add all removed entries
  @param[in] head: a list with entries
  @param[in] entry: an entry within head, could be the head itself
     and if so we won't cut the list
*/
static inline void list_cut_position(struct list_head *list,
      struct list_head *head, struct list_head *entry)
{
  if (list_empty(head))
      return;
  if (list_is_singular(head) &&
    (head->next != entry && head != entry))
    return;
  if (entry == head)
      INIT_LIST_HEAD(list);
  else
    __list_cut_position(list, head, entry);
}

static inline void __list_splice(const struct list_head *list,
             struct list_head *prev,
             struct list_head *next)
{
  struct list_head *first = list->next;
  struct list_head *last = list->prev;

  first->prev = prev;
  prev->next = first;

  last->next = next;
  next->prev = last;
}

/**
  Join two lists, this is designed for stacks
  @param[in] list: the new list to add.
  @param[in] head: the place to add it in the first list.
 */
static inline void list_splice(const struct list_head *list,
            struct list_head *head)
{
  if (!list_empty(list))
      __list_splice(list, head, head->next);
}

/**
  Join two lists, each list being a queue
  @param[in] list: the new list to add.
  @param[in] head: the place to add it in the first list.
 */
static inline void list_splice_tail(struct list_head *list,
            struct list_head *head)
{
  if (!list_empty(list))
    __list_splice(list, head->prev, head);
}

/**
  Join two lists and reinitialise the emptied list.
  @param[in] list: the new list to add.
  @param[in] head: the place to add it in the first list.
 */
static inline void list_splice_init(struct list_head *list,
              struct list_head *head)
{
  if (!list_empty(list)) {
    __list_splice(list, head, head->next);
    INIT_LIST_HEAD(list);
  }
}

/**
  Join two lists and reinitialise the emptied list
  @param[in] list: the new list to add.
  @param[in] head: the place to add it in the first list.
 */
static inline void list_splice_tail_init(struct list_head *list,
                 struct list_head *head)
{
  if (!list_empty(list)) {
    __list_splice(list, head->prev, head);
    INIT_LIST_HEAD(list);
  }
}

#undef offsetof
#define offsetof(TYPE, MEMBER) ((size_t) &((TYPE *)0)->MEMBER)

/**
   * container_of - cast a member of a structure out to the containing structure
   * @ptr:        the pointer to the member.
   * @type:       the type of the container struct this is embedded in.
   * @member:     the name of the member within the struct.
   *
   */

#define container_of(ptr, type, member) \
                      ((type *) ((char *)(ptr) - offsetof(type, member)))


/**
  Get the struct for this entry
  @param[in] ptr:  the &struct list_head pointer.
  @param[in] type:  the type of the struct this is embedded in.
  @param[in] member:  the name of the list_struct within the struct.
*/
#define list_entry(ptr, type, member) \
  container_of(ptr, type, member)

/**
  Get the first element from a list
  @param[in] ptr:  the list head to take the element from.
  @param[in] type:  the type of the struct this is embedded in.
  @param[in] member:  the name of the list_struct within the struct.
*/
#define list_first_entry(ptr, type, member) \
  list_entry((ptr)->next, type, member)


/**
* list_for_each_entry_safe - iterate over list of given type safe against removal of list entry
* @pos:        the type * to use as a loop cursor.
* @n:          another type * to use as temporary storage
* @head:       the head for your list.
* @member:     the name of the list_struct within the struct.
*/
#define list_for_each_entry_safe(pos, n, head, member)               \
	for (pos = list_entry((head)->next, __typeof__(*pos), member),      \
		n = list_entry(pos->member.next, __typeof__(*pos), member); \
		&pos->member != (head);                                    \
		pos = n, n = list_entry(n->member.next, __typeof__(*n), member))
  
  

//#endif 

#endif /* _ATLK_LIST_H */