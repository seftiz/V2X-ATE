
#ifndef __GENERAL_H__
#define __GENERAL_H__

#include <atlk/sdk.h>
#include <atlk/v2x.h>
#include <atlk/v2x_service.h>


/* Convert hex character to digit */
uint8_t hex_to_digit(char hex);

/* Convert hex of 2 character to byte */
uint8_t hex_to_byte(const char* hex);


/* Convert hex string to array of bytes */
atlk_rc_t hexstr_to_bytes_arr(const char *hexstr, size_t hexstr_len, uint8_t *buffer, size_t *buffer_len);


#endif /* __GENERAL_H__ */


